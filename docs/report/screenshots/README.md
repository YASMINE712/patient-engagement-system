# Named screenshots and evaluation figures

Captured on 29 September 2026 using isolated demo state.

| Filename | What was captured | Report location |
|---|---|---|
| 01_Personal_space_desktop.png | Desktop daily check-in and the ML navigation entry. | Fig. 4 / p. 10 |
| 02_Suggestions_and_feedback.png | Expanded suggestion steps, Helpful feedback and Save control. | Fig. 5 / p. 11 |
| 03_ML_prediction_inputs_and_results.png | Six model inputs and both saved-model prediction outputs. | Fig. 6 / p. 12 |
| 04_Regression_evaluation.png | Regression model table and prediction/residual diagnostics. | Fig. 7 / p. 13 |
| 05_Classification_metrics.png | Classification candidate comparison and metric definitions. | Fig. 8 / p. 13 |
| 06_Q_table_learning_curves.png | Cumulative simulated reward for the three interactive policies. | Fig. 9 / p. 14 |
| 07_Learned_Q_values.png | Learned state/action values from the same short run. | Fig. 10 / p. 14 |
| 08_Personal_space_mobile.png | Full mobile personal space at 390 x 844 viewport. | Screenshot package |

Generated evaluation figures are stored separately in evaluation_figures/.
Regression diagnostics, ROC/precision-recall curves, and confusion/calibration plots use the held-out HeartSteps test partition.
The Q-table screenshots use synthetic feedback (seed 2026, 300 interactions), not HeartSteps outcomes.
