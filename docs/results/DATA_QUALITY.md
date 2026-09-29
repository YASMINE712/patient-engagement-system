# Data-quality report

Pipeline version: 1.0.0
Pinned source commit: `3016391de426116bdef41880d72bc8cd4b9b2477`

Source: [HeartSteps V1](https://github.com/klasnja/HeartStepsV1), CC-BY-4.0.

## Observed HeartSteps data

| Check | Result |
|---|---|
| rows | 8274 |
| participants | 37 |
| duplicate decision keys | 0 |
| available decisions | 6590 |
| eligible decisions | 6589 |
| eligible outcome rows | 5800 |
| missing previous steps | 1012 |
| missing outcomes | 1041 |
| missing decision timestamps | 1 |
| missing scheduled timestamps | 1 |
| available unknown actions | 1 |
| sent while unavailable | 3 |
| explicit usefulness ratings | 2030 |
| invalid temperature measurements excluded from features | 35 |
| offset values exceeding plausible minutes | 8273 |

## Participant splits

Each participant belongs to exactly one split.

- test: 6 participants; 1385 decision records.
- train: 25 participants; 5526 decision records.
- validation: 6 participants; 1363 decision records.

## Interpretation limits

- Naive source utime strings are interpreted as UTC; no local-time conversion is performed.
- GMT offset magnitudes disagree with the documented minute units; offset-derived features are excluded.
- Temperature is excluded from this conservative baseline, including out-of-range values.
- Missing step outcomes are preserved, not replaced by zero.
- Recorded action flags describe delivery, not verified assignment propensities; off-policy evaluation is not enabled.
- Study day uses UTC calendar days since the first observed scheduled slot, not travel-adjusted study days.

No model was trained by this ETL command. These are data checks, not evidence of recommendation effectiveness.

## Legacy dataset

```json
{
  "rows": 374,
  "columns_original": 17,
  "unique_profiles": 132,
  "repeated_profile_rows": 242,
  "profiles_with_differing_advice": 78,
  "unique_suggestions": {
    "Stress Management": 6,
    "Sleep Hygiene": 6,
    "Exercise and Physical Activity": 6,
    "Diet and Nutrition": 5
  },
  "provenance": "Original source, recommendation-label method, and redistribution rights are unverified.",
  "note": "Literal None in Sleep Disorder is a category, not a missing value. Duplicate profiles are retained and grouped."
}
```
