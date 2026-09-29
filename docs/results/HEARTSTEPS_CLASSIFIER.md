# HeartSteps activity classification

Target: any recorded steps (>0) in the next 30 minutes. Missing outcomes are excluded.
Selected on validation ROC-AUC: random_forest. Classification threshold fixed at 0.50.

| Test candidate | ROC-AUC | AP | Accuracy | Precision | Recall | F1 | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| prevalence_baseline | 0.5000 | 0.6585 | 0.6585 | 0.6585 | 1.0000 | 0.7941 | 0.2250 |
| logistic_regression | 0.7052 | 0.7980 | 0.7052 | 0.6991 | 0.9696 | 0.8125 | 0.2009 |
| random_forest | 0.7314 | 0.8232 | 0.7419 | 0.7452 | 0.9240 | 0.8250 | 0.1884 |

Average precision (AP) summarizes precision-recall; its prevalence baseline matters.
Confusion matrices use rows=observed, columns=predicted, label order [zero steps, any steps].

## Limitations

- This is an added portfolio classification task, not the original study endpoint.
- Any recorded steps is not a health improvement label; missing outcomes are excluded.
- Six test participants limit generalization; repeated rows are not independent people.
- No oversampling or generated outcome labels; preprocessing is fitted on train only.
- Predictions condition on delivered action; they do not estimate treatment effects.
