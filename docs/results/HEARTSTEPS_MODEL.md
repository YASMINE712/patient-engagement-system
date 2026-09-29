# HeartSteps activity prediction baseline

Task: predict recorded next-window activity, conditional on profile and delivered action. This is not a treatment-effect estimate.

| Candidate | Validation MAE (steps) | Validation RMSE (log1p steps) |
|---|---:|---:|
| median_baseline | 219.27 | 2.689 |
| ridge | 215.56 | 2.463 |
| random_forest | 208.59 | 2.386 |

Selected using validation only: **random_forest**.

| Held-out test candidate | MAE (steps) | RMSE (steps) | R2 | RMSE (log1p steps) |
|---|---:|---:|---:|---:|
| median_baseline | 230.08 | 425.13 | -0.193 | 2.809 |
| ridge | 233.65 | 455.79 | -0.372 | 2.548 |
| random_forest | 216.13 | 417.04 | -0.148 | 2.434 |

## Limitations

- Only six held-out test participants; repeated rows are not independent participants.
- Observational outcome prediction is not a causal effect estimate or a recommendation policy.
- Missing outcomes are excluded; missing input values are imputed using training data only.
- No data augmentation and no test-driven hyperparameter selection.
