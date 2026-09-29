"""Public synthetic sandbox; it does not modify accounts or clinical data."""
import json
from pathlib import Path
from flask import Blueprint, jsonify, render_template, request, send_from_directory, abort
from .benchmark import demo

blueprint = Blueprint('simulation', __name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS = PROJECT_ROOT / 'reports/generated'


@blueprint.get('/simulation')
def index():
    return render_template('simulation.html')


@blueprint.get('/research')
def research():
    reports = {}
    for name in ('simulation_benchmark', 'heartsteps_model'):
        path = REPORTS / f'{name}.json'
        if path.exists():
            reports[name] = json.loads(path.read_text(encoding='utf-8'))
    return render_template('research.html', reports=reports)


@blueprint.post('/simulation/run')
def run():
    values = request.get_json(silent=True)
    if not isinstance(values, dict):
        return jsonify(error='Send a JSON object.'), 400
    seed, steps = values.get('seed', 2026), values.get('steps', 300)
    scenario = values.get('scenario', 'stationary')
    if type(seed) is not int or type(steps) is not int or not isinstance(scenario, str):
        return jsonify(error='Seed and interactions must be whole numbers; scenario must be text.'), 400
    try:
        result = demo(seed=seed, steps=steps, scenario=scenario)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(result)


@blueprint.get('/simulation/report/<name>')
def report(name):
    allowed = {'DATA_QUALITY.md', 'SIMULATION_BENCHMARK.md', 'HEARTSTEPS_MODEL.md',
               'simulation_benchmark.json', 'heartsteps_model.json', 'data_quality.json',
               'heartsteps_classifier.json', 'HEARTSTEPS_CLASSIFIER.md'}
    if name not in allowed:
        abort(404)
    return send_from_directory(REPORTS, name, as_attachment=True)
