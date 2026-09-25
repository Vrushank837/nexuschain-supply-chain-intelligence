import numpy as np

from ml.evaluate import evaluate_binary


def test_binary_metrics_are_returned():
    metrics = evaluate_binary(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]))
    assert metrics["roc_auc"] == 1.0
    assert metrics["f1"] == 1.0
    assert len(metrics["confusion_matrix"]) == 2
