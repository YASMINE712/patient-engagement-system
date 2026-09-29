# My Health Friend

A wellness planning app with personalized ideas, activity prediction, and an interactive learning lab.

**Python · Flask · scikit-learn · pandas · SQLite**

![My Health Friend - personal space](docs/report/screenshots/01_Personal_space_desktop.png)

## Features

- **Personal space:** choose a focus, find ideas that fit your time, save favorites, and give feedback.
- **ML prediction:** estimate next-window steps and the probability of recorded activity using trained Random Forest models.
- **Model evaluation:** explore ROC curves, precision, recall, F1, calibration, and regression diagnostics.
- **Learning lab:** run simulated feedback sessions and watch a contextual-bandit Q-table learn.

![ML prediction - inputs and results](docs/report/screenshots/03_ML_prediction_inputs_and_results.png)

[All screenshots](docs/report/screenshots/README.md) · [Project report](docs/report/MyHealthFriend_Updated_Report.pdf) · [Architecture](docs/ARCHITECTURE.md)

## Quick start

Use Python 3.12. In PowerShell:

```powershell
git clone https://github.com/YASMINE712/patient-engagement-system.git
cd patient-engagement-system
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe scripts/create_test_dataset.py
.\.venv\Scripts\python.exe run.py
```

Open [your personal space](http://127.0.0.1:5000/simulation). To enable ML predictions, run the training pipeline in another terminal from the project folder:

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py --download
```

Then open [ML prediction](http://127.0.0.1:5000/predict) or [the learning lab](http://127.0.0.1:5000/research). [Full setup and configuration](docs/REPRODUCIBILITY.md).

## Results

Models use participant-separated HeartSteps data. Held-out evaluation covers **899 decision windows from six participants**.

| Model | Test results |
|---|---|
| Step-count regressor | MAE **216.13 steps**, RMSE **417.04**, R2 **-0.148** |
| Activity classifier | ROC-AUC **0.731**, F1 **0.825**, accuracy **74.2%** |

The personal space uses preference and feedback ranking. Supervised models predict recorded activity; Q-table experiments use simulated feedback. The negative regression R2 and small test population remain limitations.

[Regression results](docs/results/HEARTSTEPS_MODEL.md) · [Classification results](docs/results/HEARTSTEPS_CLASSIFIER.md) · [Q-table benchmark](docs/results/SIMULATION_BENCHMARK.md)

## Development

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**42 tests**, automated GitHub checks, and desktop/mobile browser verification. [Model card](docs/MODEL_CARD.md) · [Data pipeline](docs/DATA_CONTRACT.md).

**Contributors:** Yassine Yasmine, Kassraoui Mohammed, Oumam Anass, El Mir Saad.

**Data:** [HeartSteps V1](https://github.com/klasnja/HeartStepsV1), CC-BY-4.0. This portfolio prototype does not establish clinical effectiveness.
