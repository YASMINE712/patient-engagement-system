# Repository update

The updated project continues the existing `YASMINE712/patient-engagement-system` history from commit `abb4e1d39f91e28cc9664783d4dfb90258344e7b`. It is prepared on the separate `ml-portfolio-update` branch for review before merging into `main`.

## What moved

- The legacy `app_folder/app.py` application now lives in `health_friend/web.py`, with the runnable entry point `run.py`.
- Recommendation logic is in `health_friend/recommendations.py`; templates and static files live inside `health_friend/`.
- Observed-data ETL, regression and classification are in `health_friend/data_pipeline/`.
- The model explorer is implemented in `health_friend/prediction.py`; the synthetic learning lab is in `health_friend/simulation/`.
- The report, named screenshots and evaluation figures are in `docs/report/`. Measured JSON/Markdown snapshots are in `docs/results/`.

## Files removed from the current tree

The committed `newenv/` directory is replaced by dependency declarations and a locally created environment. The legacy root questionnaire export and dataset are excluded from the updated source tree. Superseded training scripts and duplicate frontend folders are replaced by the modular implementation. Earlier commits are preserved; this update does not rewrite history.

Existing local account databases and the original project backup are not migrated or deleted. A fresh checkout uses `scripts/create_test_dataset.py` to create a clearly labeled software fixture for the legacy app, then `scripts/run_pipeline.py --download` to reproduce the separate public-data and synthetic experiments.

## Original contributors

Kassraoui Mohammed, Oumam Anass, El Mir Saad and Yassine Yasmine, as credited in the original repository. The revised report preserves the original project credits.
