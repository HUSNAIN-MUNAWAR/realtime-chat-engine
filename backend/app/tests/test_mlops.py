def test_risk_model_scores_risky_text(scorer):
    risky = scorer.predict("urgent money scam send password now")
    clean = scorer.predict("hello team the backend latency looks stable")
    assert risky["score"] >= clean["score"]
    assert risky["label"] in {"review", "risky"}
