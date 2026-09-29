# Synthetic recommendation benchmark

All users, response probabilities and outcomes in this report are simulated. No clinical effectiveness is measured.

| Scenario | Evaluation mode | Policy | Mean reward | SD across seeds | Mean cumulative regret |
|---|---|---|---:|---:|---:|
| stationary | frozen | random | 0.4176 | 0.0222 | 381.11 |
| stationary | frozen | profile_matcher | 0.3841 | 0.0229 | 304.57 |
| stationary | frozen | tabular_bandit | 0.3255 | 0.0149 | 496.67 |
| stationary | online_adaptation | random | 0.4176 | 0.0222 | 381.11 |
| stationary | online_adaptation | profile_matcher | 0.3841 | 0.0229 | 304.57 |
| stationary | online_adaptation | tabular_bandit | 0.4133 | 0.0254 | 289.26 |
| preference_shift | frozen | random | 0.4263 | 0.0179 | 377.73 |
| preference_shift | frozen | profile_matcher | 0.3165 | 0.0186 | 578.33 |
| preference_shift | frozen | tabular_bandit | 0.2904 | 0.0231 | 653.34 |
| preference_shift | online_adaptation | random | 0.4263 | 0.0179 | 377.73 |
| preference_shift | online_adaptation | profile_matcher | 0.3165 | 0.0186 | 578.33 |
| preference_shift | online_adaptation | tabular_bandit | 0.4112 | 0.0158 | 355.23 |
| high_nonresponse | frozen | random | 0.4176 | 0.0222 | 381.11 |
| high_nonresponse | frozen | profile_matcher | 0.3841 | 0.0229 | 304.57 |
| high_nonresponse | frozen | tabular_bandit | 0.3255 | 0.0149 | 496.67 |
| high_nonresponse | online_adaptation | random | 0.4176 | 0.0222 | 381.11 |
| high_nonresponse | online_adaptation | profile_matcher | 0.3841 | 0.0229 | 304.57 |
| high_nonresponse | online_adaptation | tabular_bandit | 0.3997 | 0.0187 | 321.98 |

## Protocol

- Train and validation environments use different seeds and newly generated people. Test uses a third seed range.
- Alpha is chosen using validation reward; test scenarios and seeds are fixed before comparison.
- Frozen mode does not update on test responses. Online adaptation is a separate experiment where each prediction precedes its feedback update.
- The simulator hides individual response preferences from the learner. Regret is against the best immediate expected action for the current history, not a long-term optimal policy.
- Missing feedback causes no Q update. Evaluation-only utility is retained by the runner, never passed to the learner.
- Reward SD measures variation across simulation seeds; it is not a clinical confidence interval.
- Repeated suggestions influence future response probabilities, so different policies can produce different histories.
- The strongest result need not come from the learned policy. This benchmark is intended to expose both gains and failures.
- The saved interaction CSVs come from the alpha=0.05 training runs; per-seed selected policy artifacts may use another alpha.
- Catalog content is a set of synthetic placeholders. No observed HeartSteps records were mixed into this experiment.
