"""Read-only inference from trusted, fixed local model artifacts."""
import json
import math
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, render_template, request, send_from_directory, abort
from .data_pipeline.train_baseline import FEATURES

ROOT = Path(__file__).resolve().parents[1]
blueprint = Blueprint('prediction', __name__)
FIGURES = {'regression_diagnostics.png', 'classification_roc_pr.png', 'classification_confusion_calibration.png'}
BOUNDS = {'age': (19,64), 'planned_slot': (1,5), 'study_day': (1,62), 'steps_previous_30m': (0,5380)}


def validate(values):
    if not isinstance(values, dict):
        raise ValueError('Send one input object.')
    if set(values) != set(FEATURES):
        raise ValueError('Provide exactly the six displayed model inputs.')
    clean = {}
    for key, (low, high) in BOUNDS.items():
        value = values[key]
        if key == 'steps_previous_30m' and value is None:
            clean[key] = np.nan
            continue
        if type(value) not in (int,float) or not math.isfinite(value) or not low <= value <= high or value != int(value):
            raise ValueError(f'{key} must be a whole number between {low} and {high}.')
        clean[key] = value
    for key, allowed in {'gender':('female','male'), 'action':('no_suggestion','walking','sedentary_break')}.items():
        if not isinstance(values[key],str) or values[key] not in allowed:
            raise ValueError(f'Choose a supported {key}.')
        clean[key] = values[key]
    return pd.DataFrame([clean], columns=FEATURES)


@lru_cache(maxsize=4)
def load_artifact(path, modified_ns):
    # Only callers choose a fixed local filename; no uploaded pickle is accepted.
    return joblib.load(path)


def reports():
    return {key: json.loads(path.read_text(encoding='utf-8')) for key,path in {
        'regression':ROOT/'reports/generated/heartsteps_model.json',
        'classification':ROOT/'reports/generated/heartsteps_classifier.json'}.items() if path.exists()}


@blueprint.get('/predict')
def index():
    data = reports()
    ready = all((ROOT / 'artifacts' / name).exists() for name in (
        'heartsteps_activity_model.joblib','heartsteps_activity_classifier.joblib')) and len(data) == 2
    return render_template('prediction.html', reports=data, ready=ready)


@blueprint.post('/predict/run')
def run():
    try:
        frame = validate(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    try:
        models = []
        for name in ('heartsteps_activity_model.joblib','heartsteps_activity_classifier.joblib'):
            path = ROOT / 'artifacts' / name
            models.append(load_artifact(str(path), path.stat().st_mtime_ns))
        data = reports()
        reg_name = data['regression']['selected_model']
        cls_name = data['classification']['selected_model']
    except (FileNotFoundError, KeyError):
        return jsonify(error='Train the local models first: python scripts/run_pipeline.py --download'), 503
    steps = float(np.maximum(0, np.expm1(models[0].predict(frame)[0])))
    probability = float(models[1].predict_proba(frame)[0,1])
    if not math.isfinite(steps) or not math.isfinite(probability):
        return jsonify(error='The model could not return a finite prediction.'), 500
    return jsonify(predicted_steps=round(steps,1), probability_any_steps=probability,
                   predicted_label='Any recorded steps' if probability >= .5 else 'Zero recorded steps',
                   threshold=.5, regression_model=reg_name, classification_model=cls_name,
                   source='heartsteps_v1_observed', inputs_saved=False,
                   previous_steps_imputed=bool(frame.steps_previous_30m.isna().iloc[0]))


@blueprint.get('/predict/figure/<name>')
def figure(name):
    if name not in FIGURES:
        abort(404)
    return send_from_directory(ROOT/'reports/generated', name)
