'use strict';
const form = document.getElementById('simulation-form');
const statusText = document.getElementById('status');
const names = {random: 'Random baseline', profile_matcher: 'Profile matcher', tabular_bandit: 'Learning table'};
const colors = {random: '#687c8a', profile_matcher: '#b96b19', tabular_bandit: '#087e73'};
let lastRun;
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function drawChart(run) {
  const svg = document.getElementById('learning-chart');
  svg.replaceChildren();
  const width = Math.max(300, svg.clientWidth);
  const left = 44, right = width - 12, bottom = 250;
  svg.setAttribute('viewBox', `0 0 ${width} 290`);
  function shape(tag, attributes, text) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    svg.appendChild(node);
  }
  for (let tick = 0; tick <= 4; tick++) {
    const value = tick / 4, y = bottom - value * 230;
    shape('line', {x1: left, x2: right, y1: y, y2: y, stroke: '#dce5e8'});
    shape('text', {x: left - 8, y: y + 4, 'text-anchor': 'end', fill: '#566878', 'font-size': 12}, value.toFixed(2));
  }
  Object.entries(run.results).forEach(([key, result]) => {
    const points = result.curve.map(point => `${left + point.step / run.steps * (right - left)},${bottom - point.mean_reward * 230}`).join(' ');
    shape('polyline', {points, fill: 'none', stroke: colors[key], 'stroke-width': 2.5});
  });
  shape('text', {x: left, y: 278, fill: '#566878', 'font-size': 12}, '0');
  shape('text', {x: right, y: 278, 'text-anchor': 'end', fill: '#566878', 'font-size': 12}, `${run.steps} interactions`);
}
function render(run) {
  document.getElementById('results').hidden = false;
  const cards = document.getElementById('metric-cards');
  cards.replaceChildren();
  Object.entries(run.results).forEach(([key, result]) => {
    const card = element('article', undefined, 'metric-card');
    card.append(element('h3', names[key]), element('strong', result.metrics.mean_reward.toFixed(3)),
      element('p', `Mean simulated reward | ${result.metrics.feedback_count} observed responses`));
    cards.appendChild(card);
  });
  const body = document.getElementById('q-values');
  body.replaceChildren();
  Object.entries(run.results.tabular_bandit.q_table).sort().forEach(([context, actions]) => {
    Object.entries(actions).sort().forEach(([action, value]) => {
      const row = element('tr');
      row.append(element('td', context), element('td', action), element('td', value.toFixed(3)));
      body.appendChild(row);
    });
  });
  drawChart(run);
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = document.getElementById('run');
  button.disabled = true;
  statusText.className = '';
  statusText.textContent = 'Running the seeded simulation...';
  try {
    const response = await fetch('/simulation/run', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({seed: Number(document.getElementById('seed').value), steps: Number(document.getElementById('steps').value), scenario: document.getElementById('scenario').value})});
    const run = await response.json();
    if (!response.ok) throw new Error(run.error || 'The experiment could not run.');
    lastRun = run;
    render(run);
    statusText.textContent = `Completed ${run.steps} interactions per policy. Seed ${run.seed}. Generator ${run.generator_version}.`;
  } catch (error) {
    statusText.textContent = error.message;
    statusText.className = 'error';
  } finally { button.disabled = false; }
});
document.getElementById('download').addEventListener('click', () => {
  if (!lastRun) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(lastRun, null, 2)], {type: 'application/json'}));
  const link = element('a');
  link.href = url;
  link.download = `synthetic-simulation-${lastRun.seed}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
window.addEventListener('resize', () => { if (lastRun) drawChart(lastRun); });
