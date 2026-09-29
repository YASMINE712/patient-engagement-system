# Data sources and boundaries

## Existing local CSV

`raw/legacy_wellness.csv` is a byte-for-byte copy of the original 374-row project CSV. Its original source and redistribution license have not been verified. The word "scientifically" in its old filename is not evidence of clinical validation.

This file is available locally but excluded from Git until provenance is established. Do not upload private questionnaire submissions or account databases.

## CI fixture

`python scripts/create_test_dataset.py` generates a tiny explicitly synthetic software-test fixture when the local CSV is absent. It refuses to overwrite existing data. Its suggestions are placeholders, not wellness advice, and its purpose is only to test application wiring.

## Observed dataset

HeartSteps V1: https://github.com/klasnja/HeartStepsV1

The source repository lists CC-BY-4.0 and provides the required study citation. The source revision and file hashes are pinned in sources/heartsteps-v1.json. DATA_CONTRACT.md documents the schema, eligibility checks, outcome windows and unresolved assignment/delivery details. Off-policy causal evaluation is not implemented. Do not treat 8,274 decision records as 8,274 independent participants.

## Synthetic benchmark

Store generated interactions under `synthetic/`, separately from observed study data. Each run must record the seed, generator version, scenario, source type, and configuration. A synthetic reward is a simulator output, not a patient outcome. Hold out users and scenarios; hide reward parameters from the learner.

Processed datasets, downloaded raw files, runtime state, and generated model artifacts are excluded from Git by default. Version their manifests and checksums instead.

Run `python scripts/run_pipeline.py --download` for the complete experiment. Generated synthetic logs contain explicit source, generator version, seed and split fields.
