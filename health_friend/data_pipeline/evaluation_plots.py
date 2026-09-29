"""Saved evaluation figures; no plotting service or user data collection."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix

plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.facecolor': 'white', 'axes.titleweight': 'bold'})
COLORS = ['#8a7964', '#3b7b95', '#285749']


def save(fig, folder, name):
    fig.tight_layout(pad=1.6)
    fig.savefig(folder / name, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return name


def regression_plots(model, frame, features, folder, name):
    actual = frame['steps_next_30m'].to_numpy(float)
    predicted = np.maximum(0, np.expm1(model.predict(frame[features])))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].scatter(actual, predicted, s=15, alpha=.35, color=COLORS[2])
    bound = max(actual.max(), predicted.max())
    axes[0].plot([0, bound], [0, bound], '--', color=COLORS[0], label='Perfect prediction')
    axes[0].set(xlabel='Observed steps (next 30 minutes)', ylabel='Predicted steps', title='Observed vs predicted')
    axes[0].legend(fontsize=9)
    axes[1].scatter(predicted, actual-predicted, s=15, alpha=.35, color=COLORS[1])
    axes[1].axhline(0, linestyle='--', color=COLORS[0])
    axes[1].set(xlabel='Predicted steps', ylabel='Residual: observed minus predicted', title='Residuals on the original step scale')
    fig.suptitle(f'Held-out regression diagnostics | {name} | {len(frame)} rows / {frame.participant_id.nunique()} participants', fontsize=12)
    return [save(fig, folder, 'regression_diagnostics.png')]


def classification_plots(actual, probabilities, selected, folder):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for (name, probability), color in zip(probabilities.items(), COLORS):
        fpr, tpr, _ = roc_curve(actual, probability)
        precision, recall, _ = precision_recall_curve(actual, probability)
        axes[0].plot(fpr, tpr, label=name, color=color)
        axes[1].plot(recall, precision, label=name, color=color)
    axes[0].plot([0,1],[0,1], '--', color='#b9b9b9', label='Chance ranking')
    axes[0].set(xlabel='False positive rate', ylabel='True positive rate (recall)', title='ROC curves', xlim=(0,1), ylim=(0,1.02))
    axes[1].axhline(actual.mean(), linestyle='--', color='#b9b9b9', label='Test positive prevalence')
    axes[1].set(xlabel='Recall', ylabel='Precision', title='Precision-recall curves', xlim=(0,1), ylim=(0,1.02))
    for ax in axes: ax.legend(fontsize=8, loc='lower right')
    plots = [save(fig, folder, 'classification_roc_pr.png')]
    probability = probabilities[selected]
    matrix = confusion_matrix(actual, probability >= .5, labels=[0,1])
    fig, axes = plt.subplots(1, 2, figsize=(11,4.6))
    axes[0].imshow(matrix, cmap='Greens')
    for i in range(2):
        for j in range(2):
            axes[0].text(j, i, str(matrix[i,j]), ha='center', va='center', fontsize=20,
                         color='white' if matrix[i,j] > matrix.max()*.6 else '#183e36')
    axes[0].set(xticks=[0,1], yticks=[0,1], xticklabels=['Zero steps','Any steps'],
                yticklabels=['Zero steps','Any steps'], xlabel='Predicted label', ylabel='Observed label',
                title='Confusion matrix | threshold 0.50')
    observed, predicted = calibration_curve(actual, probability, n_bins=8, strategy='quantile')
    axes[1].plot(predicted, observed, 'o-', color=COLORS[2], label=selected)
    axes[1].plot([0,1],[0,1], '--', color=COLORS[0], label='Perfect calibration')
    axes[1].set(xlabel='Mean predicted probability', ylabel='Observed fraction with any steps',
                xlim=(0,1), ylim=(0,1), title='Reliability diagram | quantile bins')
    axes[1].legend(fontsize=9)
    plots.append(save(fig, folder, 'classification_confusion_calibration.png'))
    return plots
