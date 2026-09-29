# Data contract and ETL

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m health_friend.data_pipeline.cli --download
```

The first run downloads missing files from a pinned HeartSteps revision. Later runs use the local files and verify their SHA-256 hashes. Omit `--download` to require an offline run. The source manifest is `data/sources/heartsteps-v1.json`.

## Scope

The initial real-data task is analysis of decision records and subsequent recorded activity. It is not yet a learned policy or a claim of treatment effectiveness. Only the user and suggestion tables are downloaded; the larger minute-level sensor files are unnecessary for this initial aggregation.

## Sources and attribution

- [HeartSteps V1 repository](https://github.com/klasnja/HeartStepsV1), licensed CC-BY-4.0. Original files and license are kept locally without modification.
- Klasnja et al. (2019), Efficacy of Contextually Tailored Suggestions for Physical Activity: A Micro-randomized Optimization Trial of HeartSteps. DOI: https://doi.org/10.1093/abm/kay067
- [Suggestion table dictionary](https://github.com/klasnja/HeartStepsV1/wiki/Documentation-for-suggestions.csv).
- [User table dictionary](https://github.com/klasnja/HeartStepsV1/wiki/Documentation-for-users.csv).

Our processed tables are transformations: selected columns, renamed fields, typed values, a validated participant join, eligibility flags, and deterministic participant splits. Dictionaries are interpreted with the observed file contents; discrepancies are explicitly reported.

## Primary keys and joins

`users.csv`: one row per `user.index`. `suggestions.csv`: unique `(user.index, decision.index)`, including zero-valued decision indices. Join many-to-one on participant ID. Duplicated keys or unmatched participants cause validation failure rather than row multiplication or silent loss.

## Model input allowlist

| Output | Source | Availability and handling |
|---|---|---|
| age | users.age | Intake; required integer |
| gender | users.gender | Intake; retain source category |
| planned_slot | sugg.select.slot | Planned time slot 1-5, before delivery |
| study_day | sugg.select.utime | UTC calendar day since that participant's first observed planned slot |
| steps_previous_30m | jbsteps30pre | Source pre-decision aggregate; missing is preserved |

Participant and decision IDs are join keys, not prediction features. Intake timestamps must precede planned decisions. Context recorded after the observed decision triggers validation failure. The dictionary contains an apparent inconsistency in the description of `jbsteps30pre`; its name and surrounding window definitions support the 30-minute interpretation, which should be checked against study analysis code before inferential modeling.

## Labels and audit fields

- `action`: no_suggestion, walking, sedentary_break, or unknown, reconstructed from delivery flags. Contradictory or missing flags produce unknown.
- `steps_next_30m`: un-imputed Jawbone post-decision count. Missing is not inactivity.
- `usefulness_rating`: good=1, bad=0. No response, snooze, and absent response remain missing.
- `available`, delivery and timestamp fields: audit/eligibility information.
- `eligible_decision`: available, known action, and known scheduled/observed decision timestamps.
- `eligible_outcome_analysis`: eligible decision with observed step outcome.

The complete decision table retains excluded records for audit. The feature/label exports include only eligible decisions, with identical join keys. Labels with missing outcomes remain explicitly marked; a later training task must choose the appropriate observed-label subset.

No response fields, exit surveys, future step counts, or delivery actions enter the profile feature allowlist. A later action-conditioned outcome model must add action deliberately and document the resulting task.

## Missingness and source discrepancies

The source contains missing timestamps, missing measurements, and an unknown delivered action. These are retained and reported. Temperature values outside -90 to 60 degrees Celsius are flagged; temperature is excluded entirely from the first feature set. Offset values look like seconds, whereas the wiki describes minutes; no local-hour feature is derived. Naive `utime` strings are parsed as UTC by explicit project convention, not by the machine's timezone.

The documented trial probabilities are not automatically assigned to observed delivery flags. The exact relationship between assignment, availability, delivery and suggestion type must be reconciled before off-policy evaluation. Unsent actions do not receive fabricated outcomes.

## Splits and outputs

Participants are sorted by a seed-dependent SHA-256 ordering and assigned approximately 70/15/15 to train/validation/test. All decisions from one person stay together. Default seed 2026 gives 25/6/6 participants. This assesses new-participant generalization; a temporal adaptation experiment will need a separately specified split.

Outputs under `data/processed/heartsteps-v1/`:

- `decisions.csv`: full audit table.
- `features.csv`: conservative feature allowlist plus keys and split.
- `labels.csv`: actions, outcomes, outcome-observed flag and explicit ratings.
- `participant_splits.csv`: reproducible participant assignment.

`reports/generated/data_quality.json` contains row counts, missingness, split counts and output hashes. `DATA_QUALITY.md` is the readable summary. Generated data and reports are ignored by Git; source manifests and this contract are versioned.

## Legacy data

The existing CSV is cleaned separately. Normalize Normal Weight to Normal, extract blood pressure components, retain the literal None sleep-disorder category, and group repeated profiles without deleting them. Unknown source/license and inconsistent recommendation labels remain documented limitations. A small CI software fixture is recognized and skipped by the legacy audit. Its content must not be counted as observed data.
