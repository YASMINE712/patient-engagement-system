# Architecture

```text
Pinned HeartSteps files
  -> checksum verification
  -> schema validation and participant join
  -> separate feature/label tables and participant splits
  -> training-only preprocessing
  -> median / Ridge / Random Forest comparison
  -> held-out prediction report and candidate model artifact
  -> separate any-recorded-steps classifier and classification evaluation
  -> /predict: read-only inference from both saved artifacts

Seeded synthetic users + labeled demo catalog
  -> eligibility filter
  -> random / fixed matcher / tabular bandit
  -> simulated response (including missing feedback)
  -> immediate-reward update
  -> held-out and online-adaptation benchmarks
  -> reports, per-run policy artifacts and training interaction logs

User-facing personal space (/simulation)
  -> authored sample planning catalog
  -> goal and available-time filters
  -> deterministic style and feedback ranking
  -> browser-local preferences, ratings and saved ideas

Flask Learning Lab (/research)
  -> displays saved experiment reports
  -> runs bounded synthetic episodes
  -> shows reward curves and Q-values
  -> downloads run JSON
```

`health_friend/data_pipeline` contains ingestion, contracts, transformations and real-data baseline training. `health_friend/simulation` contains the simulator, policies, benchmark and Flask blueprint. Neither training path accesses the legacy app's account database.

The personal space uses `templates/simulation.html` and `static/js/simulation.js`. Its browser-local ranking is separate from both trained research models. The research page uses `templates/research.html` and `static/js/research.js`; the bounded experiment API remains at `/simulation/run` and report downloads at `/simulation/report/<name>`.

`health_friend/prediction.py` serves the model explorer and `/predict/run` API, validates six inputs, loads only known local artifact paths, and exposes an allowlist of generated evaluation figures. The request does not write account, questionnaire, or model state. `train_classifier.py` owns the added binary target and participant-level uncertainty estimate; `evaluation_plots.py` produces the regression and classification figures.

The legacy Flask questionnaire app is retained as a separate baseline experience. It uses `health_friend/recommendations.py`, the local legacy CSV, and private runtime state under `instance/`.

Tests use synthetic fixtures and isolated temporary databases. CI does not require private data or download the real study. Source manifests, tests and experiment code are versioned; downloaded data, private records and generated artifacts are ignored by Git.
