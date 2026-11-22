from pathlib import Path

from scripts.generate_runtime_evidence import load_samples, run_trace
from app.ml.risk_model import NaiveBayesRiskScorer


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_trace_uses_checked_in_model_and_all_samples() -> None:
    samples = load_samples(ROOT / "mlops/data/chat_risk_samples.csv")
    scorer = NaiveBayesRiskScorer(str(ROOT / "mlops/models/current/risk_model.json"))

    trace = run_trace(samples, scorer)

    assert len(trace) == 15
    assert {row["model_version"] for row in trace} == {"nb-risk-v1"}
    assert all(row["predicted_label"] in {"clean", "review", "risky"} for row in trace)
    assert sum(row["expected_label"] == row["predicted_label"] for row in trace) == 15
