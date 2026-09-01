"""
ai/tests/evaluation/test_evaluation_harness.py

Tests the quantitative evaluation harness for accuracy and citation validity metrics.
"""

from src.evaluation.eval_runner import EvaluationRunner


def test_evaluation_benchmark_run():
    runner = EvaluationRunner()
    metrics = runner.run_benchmark()

    assert metrics["total_test_cases"] >= 5
    assert metrics["accuracy_rate"] >= 0.80
    assert metrics["citation_validity_rate"] >= 0.80
    assert len(metrics["details"]) == metrics["total_test_cases"]
