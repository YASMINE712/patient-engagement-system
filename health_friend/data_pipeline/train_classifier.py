"""Secondary target: any recorded steps (>0) in the next 30 minutes."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, average_precision_score, brier_score_loss,
                             log_loss, confusion_matrix)
from .train_baseline import make_pipeline, FEATURES
from .sources import sha256


def binary_target(frame):
    target = frame['steps_next_30m']
    if target.isna().any() or not np.isfinite(target).all() or (target < 0).any():
        raise ValueError('Classification needs observed nonnegative outcomes; missing is not zero.')
    return target.gt(0).to_numpy(dtype=int)


def metrics(actual, probability):
    predicted = probability >= .5
    return {'rows': len(actual), 'positive_rows': int(actual.sum()), 'positive_prevalence': float(actual.mean()),
            'accuracy': float(accuracy_score(actual, predicted)),
            'balanced_accuracy': float(balanced_accuracy_score(actual, predicted)),
            'precision': float(precision_score(actual, predicted, zero_division=0)),
            'recall': float(recall_score(actual, predicted, zero_division=0)),
            'f1': float(f1_score(actual, predicted, zero_division=0)),
            'roc_auc': float(roc_auc_score(actual, probability)),
            'average_precision': float(average_precision_score(actual, probability)),
            'brier_score': float(brier_score_loss(actual, probability)),
            'log_loss': float(log_loss(actual, probability, labels=[0,1])),
            'confusion_matrix': confusion_matrix(actual, predicted, labels=[0,1]).tolist()}


def cluster_auc_interval(actual, probability, participants, repeats=1000):
    """Resample whole participants, retaining each selected participant's rows."""
    rng = np.random.default_rng(2026)
    groups = np.unique(participants)
    indices = {group: np.flatnonzero(participants == group) for group in groups}
    scores = []
    for _ in range(repeats):
        idx = np.concatenate([indices[g] for g in rng.choice(groups, size=len(groups), replace=True)])
        if len(np.unique(actual[idx])) == 2:
            scores.append(roc_auc_score(actual[idx], probability[idx]))
    low, high = np.quantile(scores, [.025,.975])
    return {'low': float(low), 'high': float(high), 'valid_resamples': len(scores),
            'requested_resamples': repeats, 'method': 'participant-cluster percentile bootstrap',
            'seed': 2026, 'warning': 'Only six test participants; this interval is exploratory.'}


def train(root):
    root = Path(root)
    dataset = root / 'data/processed/heartsteps-v1/decisions.csv'
    frame = pd.read_csv(dataset)
    frame = frame.loc[frame['eligible_outcome_analysis'].eq(True)].copy()
    parts = {s: frame.loc[frame['split'].eq(s)] for s in ('train','validation','test')}
    sets = [set(p['participant_id']) for p in parts.values()]
    if any(sets[i] & sets[j] for i in range(3) for j in range(i+1,3)):
        raise ValueError('Participant leakage between splits')
    targets = {s: binary_target(p) for s,p in parts.items()}
    if any(len(np.unique(y)) != 2 for y in targets.values()):
        raise ValueError('Both classes are required in each split')
    estimators = {'prevalence_baseline': DummyClassifier(strategy='prior'),
                  'logistic_regression': LogisticRegression(C=1.0, max_iter=1000, random_state=2026),
                  'random_forest': RandomForestClassifier(n_estimators=150, max_depth=8,
                                                         min_samples_leaf=10, random_state=2026, n_jobs=1)}
    fitted, validation = {}, {}
    for name, estimator in estimators.items():
        model = make_pipeline(estimator).fit(parts['train'][FEATURES], targets['train'])
        validation[name] = metrics(targets['validation'], model.predict_proba(parts['validation'][FEATURES])[:,1])
        fitted[name] = model
    winner = max(validation, key=lambda name: validation[name]['roc_auc'])
    probabilities = {name: m.predict_proba(parts['test'][FEATURES])[:,1] for name,m in fitted.items()}
    test = {name: metrics(targets['test'], p) for name,p in probabilities.items()}
    from .evaluation_plots import classification_plots
    folder = root / 'reports/generated'
    folder.mkdir(parents=True, exist_ok=True)
    (root / 'artifacts').mkdir(exist_ok=True)
    joblib.dump(fitted[winner], root / 'artifacts/heartsteps_activity_classifier.joblib')
    report = {'source':'heartsteps_v1_observed', 'task':'Any recorded steps in the next 30 minutes',
              'target':'steps_next_30m > 0', 'positive_label':'Any recorded steps', 'negative_label':'Zero recorded steps',
              'threshold':.5, 'threshold_protocol':'Fixed at 0.50 before fitting; not tuned on the test set.',
              'selected_model':winner, 'selection_metric':'Maximum validation ROC-AUC', 'features':FEATURES,
              'partitions': {s:{'rows':len(p), 'participants':int(p.participant_id.nunique()),
                                'positive_rows':int(targets[s].sum())} for s,p in parts.items()},
              'validation':validation, 'test_candidates':test,
              'selected_roc_auc_95_interval':cluster_auc_interval(targets['test'],probabilities[winner],parts['test'].participant_id.to_numpy()),
              'plots': classification_plots(targets['test'],probabilities,winner,folder),
              'sklearn_version':sklearn.__version__, 'processed_dataset_sha256':sha256(dataset),
              'limitations':['This is an added portfolio classification task, not the original study endpoint.',
                            'Any recorded steps is not a health improvement label; missing outcomes are excluded.',
                            'Six test participants limit generalization; repeated rows are not independent people.',
                            'No oversampling or generated outcome labels; preprocessing is fitted on train only.',
                            'Predictions condition on delivered action; they do not estimate treatment effects.']}
    (folder / 'heartsteps_classifier.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines = ['# HeartSteps activity classification','',
             'Target: any recorded steps (>0) in the next 30 minutes. Missing outcomes are excluded.',
             f'Selected on validation ROC-AUC: {winner}. Classification threshold fixed at 0.50.','',
             '| Test candidate | ROC-AUC | AP | Accuracy | Precision | Recall | F1 | Brier |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in test.items():
        lines.append('| '+name+' | '+' | '.join(f'{m[key]:.4f}' for key in ['roc_auc','average_precision','accuracy','precision','recall','f1','brier_score'])+' |')
    lines += ['', 'Average precision (AP) summarizes precision-recall; its prevalence baseline matters.',
              'Confusion matrices use rows=observed, columns=predicted, label order [zero steps, any steps].','',
              '## Limitations',''] + ['- '+item for item in report['limitations']]
    (folder / 'HEARTSTEPS_CLASSIFIER.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    print(json.dumps(train(parser.parse_args().root), indent=2))
