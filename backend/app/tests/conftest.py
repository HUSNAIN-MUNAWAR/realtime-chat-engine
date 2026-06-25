import pytest
from app.ml.risk_model import NaiveBayesRiskScorer

@pytest.fixture()
def scorer():
    return NaiveBayesRiskScorer(model_path="/app/mlops/models/current/risk_model.json")
