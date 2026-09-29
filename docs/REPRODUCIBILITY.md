# Reproduction and review

## Environment

Python 3.12 is the tested local runtime. Install `requirements-lock.txt` in a fresh virtual environment. `requirements.txt` lists direct requirements. Package version locks are version pins, not cryptographic supply-chain locks.

## Full experiment

```powershell
python scripts/run_pipeline.py --download
```

This verifies/downloads a pinned HeartSteps snapshot, runs ETL, trains and evaluates an activity-count predictor, and runs the synthetic recommendation benchmark. After the first download, `python scripts/run_pipeline.py` works from cached data and verifies the source checksums.

It writes separate reports under `reports/generated/` and separate model artifacts under `artifacts/`. `pipeline_run.json` records report hashes. Intermediate real data goes into `data/processed/heartsteps-v1/`; simulator logs go into `data/synthetic/`.

The full simulation uses five fixed seeds. `--quick` is a smaller software smoke run and must not be presented as the full benchmark. It overwrites the generated experiment reports, so rerun the full command before presenting final results.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover application flows, policy updates, missing feedback, simulator determinism, feature separation, participant joins, split reproducibility, source-tamper detection, train-only preprocessing and the no-emojis requirement. No private database or network access is required by unit tests. A fresh checkout can run `python scripts/create_test_dataset.py` for the legacy app fixture.

The local browser smoke check additionally exercised desktop/mobile layouts, chart rendering, Q-table display and JSON export in Microsoft Edge. This browser check is not currently part of hosted CI.

## Docker demo

```powershell
docker build -t my-health-friend .
docker run --rm -p 127.0.0.1:5000:5000 my-health-friend
```

The container excludes private data and uses the labeled software fixture for the legacy app. The Learning Lab's interactive simulator requires no real study files. Docker is not available on the development host, so the image definition has not been built or run here. The Flask server configuration is for a local demonstration, not production hosting.

## Publication boundaries

Do not commit account databases, secrets, raw study files, generated user logs, or Python environments. The original dataset's provenance remains unresolved; it is kept local. The HeartSteps source manifest, attribution, contracts, aggregate report snapshots, code and tests can be reviewed separately from downloaded data. Confirm the inherited project's code rights before assigning a repository-wide license.

GitHub workflows are configured, but a hosted run has not occurred until the repository is published. No remote repository is created or pushed automatically.

## CV description based on completed scope

My Health Friend - Prototype de recommandation adaptative : pipeline ETL reproductible sur des donnees longitudinales publiques, comparaison de modeles de prediction avec separation par participant, evaluation de bandits contextuels sur utilisateurs simules et interface Flask de visualisation de l'apprentissage.

Describe simulated results explicitly. Do not claim clinical validation or an improvement over every baseline.
