# Model and simulator card

## Intended use

Portfolio demonstration of ETL, tabular prediction, online reward estimation, reproducible evaluation, and a Flask experiment interface. This is not a clinical decision tool.

## Observed-data model

HeartSteps V1 records are transformed according to `DATA_CONTRACT.md`. The regression target is log1p of recorded Jawbone steps in the next 30-minute window. Inputs are a conservative profile/history allowlist plus the recorded delivered action. A median baseline, Ridge regression, and Random Forest are compared on validation participants. The candidate with the lowest validation MAE in original step units is selected. The update reports all fixed candidates on test participants without retuning. Metrics include step-scale MAE, RMSE, R2 and log-scale RMSE; residual plots expose large-count underprediction.

Imputation, scaling and category encoding are fit on training rows only. Missing outcomes are excluded rather than imputed. All records from one participant remain in the same split. The target is an observed count; predictions are not estimates of how much an intervention helps. Action assignment/delivery discrepancies and the small held-out population limit interpretation.

Artifact: `artifacts/heartsteps_activity_model.joblib`. It contains a local fitted preprocessing/model pipeline and should only be loaded from a trusted experiment run. `reports/generated/heartsteps_model.json` records input features, data checksum, package version and measured results.

## Secondary binary classifier

The added portfolio task predicts whether an eligible observed next-window count is greater than zero. It is not the original study endpoint or a measure of usefulness. Missing outcomes are excluded; zero recorded steps is the negative class. A prior-probability baseline, logistic regression (C=1), and Random Forest (150 trees, depth 8, leaf size 10) are fit on training participants. Validation ROC-AUC selects the model; the decision threshold is fixed at 0.50. No test-driven tuning or outcome augmentation is used.

Test metrics include ROC-AUC, average precision, accuracy, balanced accuracy, precision, recall, F1, Brier score and log loss. Saved plots show ROC, precision-recall, the selected model's confusion matrix and quantile-bin calibration. The exploratory AUC interval resamples entire participants 1,000 times using seed 2026. Only six people form the test set, so the interval does not establish broad generalization. Artifact: `artifacts/heartsteps_activity_classifier.joblib`; report: `reports/generated/heartsteps_classifier.json`.

## Interactive inference

`/predict` loads the two fixed, trusted local artifacts and returns predictions without saving inputs. It constrains numeric input to the observed training bounds and supports missing previous-window steps via the fitted imputer. The delivered-action field describes context; comparing its predictions is not causal policy optimization. The public personal-space catalog and its browser-local ranking remain separate from both supervised models. No feedback button retrains the forest. Retraining is an explicit pipeline run.

## Synthetic environment

Version 1.0.0 creates fictional users with a goal, a time budget, and a stated interaction preference. Private variables include a response preference and an individual response offset. The stated preference agrees with the hidden preference probabilistically. The model never receives those private variables.

The reward probability is an engineering assumption: a base response probability plus a preference-match contribution and an individual offset, reduced by recent repetition. A Bernoulli draw produces utility, and an independent response process determines whether the learner observes that utility. The benchmark keeps unobserved utility only for evaluation. These relationships do not claim to represent clinical behavior.

Actions are stable IDs for twelve synthetic planning activities across four categories. They are deliberately labeled demo placeholders, with no clinical review claim. Eligibility respects goal and time budget. Scenario changes include shifted private preferences and more frequent missing feedback.

## Policies

- Random baseline: uniform selection among eligible actions.
- Profile matcher: deterministic choice based on stated preference and duration.
- Tabular contextual bandit: estimates immediate simulated reward for `(goal, budget, preference, action)`. Initial values are 0.5. Update: `Q = Q + alpha * (feedback - Q)`. Missing feedback skips the update. This is immediate-reward learning, not a model of long-term health transitions.

The training policy uses epsilon=0.1 exploration. Alpha is selected from 0.05 and 0.15 using validation users. Frozen evaluation disables exploration and updates. Online adaptation is reported separately and predicts before each update. The interactive sandbox starts from an empty table each time and must not be confused with the pretrained benchmark.

## Evaluation

Five fixed seeds, separate training/validation/test user populations, and three fixed scenarios are recorded in the benchmark JSON. Report mean simulated utility, variation across seeds, and cumulative regret relative to a best immediate action with access to the simulator. This oracle is not a long-term optimal policy. Different policies change repetition histories.

The initial table groups users coarsely and does not include recent action history in its state. It can miss individual differences and fatigue effects. A lower reward than a simple or random baseline is a valid result and must remain visible. Do not describe a policy as best without qualifying the scenario and evaluation mode.

## Boundaries

- HeartSteps records and simulated rewards are never combined into a single training dataset.
- No synthetic row is presented as a real participant or a health outcome.
- Augmentation is not used to fabricate outcome labels. The simulator is an explicit separate experiment.
- Frozen test evaluation is not reused to select hyperparameters.
- If future development is guided by these test results, treat the current benchmark as exploratory and define a new final evaluation protocol.
- The legacy app's row-based Q-table remains isolated in `instance/`; it is not relabeled as the new simulator's policy.

## Retraining and deployment

Run the full pipeline manually to produce candidate artifacts and reports. This version does not automatically promote a model into the legacy wellness app and does not run scheduled retraining. The dashboard shows experiment results and supports bounded simulated runs. Automatic promotion would need acceptance thresholds, rollback, and validation with appropriate real feedback data.
