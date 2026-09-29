"use strict";
const form = document.getElementById('prediction-form');
const status = document.getElementById('prediction-status');
const submit = document.getElementById('predict-button');
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const fields = new FormData(form);
  const values = Object.fromEntries(fields);
  for (const name of ['age','planned_slot','study_day','steps_previous_30m']) {
    values[name] = fields.get(name) === '' ? null : Number(fields.get(name));
  }
  submit.disabled = true;
  status.textContent = 'Running the trained models...';
  document.getElementById('prediction-result').hidden = true;
  document.getElementById('prediction-empty').hidden = false;
  try {
    const response = await fetch('/predict/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(values)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Prediction is unavailable. Please try again.');
    document.getElementById('predicted-steps').textContent = result.predicted_steps.toLocaleString(undefined,{maximumFractionDigits:1});
    document.getElementById('activity-probability').textContent = (100*result.probability_any_steps).toFixed(1)+'%';
    document.getElementById('activity-label').textContent = result.predicted_label+' / threshold 0.50';
    document.getElementById('model-names').textContent = 'Step model: '+result.regression_model.replaceAll('_',' ')+'. Activity model: '+result.classification_model.replaceAll('_',' ')+'.';
    document.getElementById('imputation-note').textContent = result.previous_steps_imputed ? 'Previous steps were missing: the model used its training-data imputation.' : '';
    document.getElementById('prediction-result').hidden = false;
    document.getElementById('prediction-empty').hidden = true;
    status.textContent = 'Prediction ready. Your inputs were not saved.';
  } catch (error) {
    status.textContent = error.message;
  } finally { submit.disabled = false; }
});
