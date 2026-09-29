"""Predict recorded next-window activity; this does not estimate treatment benefit."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .sources import sha256
from .transform import HEARTSTEPS_FEATURES

NUMERIC = ['age', 'planned_slot', 'study_day', 'steps_previous_30m']
CATEGORICAL = ['gender', 'action']
FEATURES = HEARTSTEPS_FEATURES + ['action']


def make_pipeline(estimator):
    numeric = Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True)), ('scale', StandardScaler())])
    categorical = Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                            ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False))])
    transform = ColumnTransformer([('numeric', numeric, NUMERIC), ('categorical', categorical, CATEGORICAL)])
    return Pipeline([('preprocess', transform), ('model', estimator)])


def evaluate(model, frame):
    actual = frame['steps_next_30m'].to_numpy(dtype=float)
    log_prediction = model.predict(frame[FEATURES])
    prediction = np.maximum(0, np.expm1(log_prediction))
    return {'rows': len(frame), 'participants': int(frame['participant_id'].nunique()),
            'mae_steps': float(mean_absolute_error(actual, prediction)),
            'rmse_steps': float(np.sqrt(mean_squared_error(actual, prediction))),
            'r2': float(r2_score(actual, prediction)),
            'rmse_log1p_steps': float(np.sqrt(mean_squared_error(np.log1p(actual), log_prediction)))}


def train(root):
    root = Path(root)
    dataset = root / 'data/processed/heartsteps-v1/decisions.csv'
    frame = pd.read_csv(dataset)
    selected = frame.loc[frame['eligible_outcome_analysis'].eq(True)].copy()
    partitions = {split: selected.loc[selected['split'].eq(split)] for split in ('train', 'validation', 'test')}
    for split, part in partitions.items():
        if part.empty:
            raise ValueError(f'No eligible outcomes in {split}')
    sets = [set(part['participant_id']) for part in partitions.values()]
    if any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError('Participant leakage between splits')
    estimators = {'median_baseline': DummyRegressor(strategy='median'), 'ridge': Ridge(alpha=1.0),
                  'random_forest': RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=10,
                                                         random_state=2026, n_jobs=1)}
    fitted, validation = {}, {}
    for name, estimator in estimators.items():
        model = make_pipeline(estimator)
        model.fit(partitions['train'][FEATURES], np.log1p(partitions['train']['steps_next_30m'].to_numpy(dtype=float)))
        validation[name] = evaluate(model, partitions['validation'])
        fitted[name] = model
    winner = min(validation, key=lambda name: validation[name]['mae_steps'])
    test = {'selected_model': evaluate(fitted[winner], partitions['test']),
            'median_baseline': evaluate(fitted['median_baseline'], partitions['test'])}
    test_candidates = {name: evaluate(model, partitions['test']) for name, model in fitted.items()}
    artifact_dir = root / 'artifacts'
    artifact_dir.mkdir(exist_ok=True)
    joblib.dump(fitted[winner], artifact_dir / 'heartsteps_activity_model.joblib')
    report = {'source': 'heartsteps_v1_observed', 'task': 'predict recorded steps in the next 30-minute window given context and delivered action',
              'selection_metric': 'validation MAE in steps', 'selected_model': winner, 'features': FEATURES,
              'target': 'log1p(steps_next_30m)', 'validation': validation, 'test': test,
              'test_candidates': test_candidates,
              'sklearn_version': sklearn.__version__, 'processed_dataset_sha256': sha256(dataset),
              'limitations': ['Only six held-out test participants; repeated rows are not independent participants.',
                              'Observational outcome prediction is not a causal effect estimate or a recommendation policy.',
                              'Missing outcomes are excluded; missing input values are imputed using training data only.',
                              'No data augmentation and no test-driven hyperparameter selection.']}
    folder = root / 'reports/generated'
    folder.mkdir(parents=True, exist_ok=True)
    from .evaluation_plots import regression_plots
    report['plots'] = regression_plots(fitted[winner], partitions['test'], FEATURES, folder, winner)
    (folder / 'heartsteps_model.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = ['# HeartSteps activity prediction baseline', '',
             'Task: predict recorded next-window activity, conditional on profile and delivered action. This is not a treatment-effect estimate.', '',
             '| Candidate | Validation MAE (steps) | Validation RMSE (log1p steps) |', '|---|---:|---:|']
    for name, metrics in validation.items():
        lines.append(f"| {name} | {metrics['mae_steps']:.2f} | {metrics['rmse_log1p_steps']:.3f} |")
    lines += ['', f'Selected using validation only: **{winner}**.', '',
              '| Held-out test candidate | MAE (steps) | RMSE (steps) | R2 | RMSE (log1p steps) |', '|---|---:|---:|---:|---:|']
    for name, metrics in test_candidates.items():
        lines.append(f"| {name} | {metrics['mae_steps']:.2f} | {metrics['rmse_steps']:.2f} | {metrics['r2']:.3f} | {metrics['rmse_log1p_steps']:.3f} |")
    lines += ['', '## Limitations', ''] + [f'- {item}' for item in report['limitations']]
    (folder / 'HEARTSTEPS_MODEL.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(json.dumps(train(args.root), indent=2))
