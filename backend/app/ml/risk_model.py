from __future__ import annotations
import json, math, time
from pathlib import Path
from app.core.config import settings
from app.observability.metrics import ML_LATENCY, ML_PREDICTIONS

class NaiveBayesRiskScorer:
    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = Path(model_path or settings.risk_model_path)
        self.model = self._load_model()

    def _load_model(self) -> dict:
        if self.model_path.exists():
            try:
                model = json.loads(self.model_path.read_text(encoding="utf-8"))
                if model:
                    return model
            except Exception:
                pass
        return {
            "version": "fallback-rules-v0",
            "labels": ["clean", "risky"],
            "priors": {"clean": 0.5, "risky": 0.5},
            "token_log_probs": {"clean": {}, "risky": {}},
            "unknown_log_probs": {"clean": math.log(1e-5), "risky": math.log(1e-5)},
            "risk_keywords": ["spam", "scam", "hate", "attack", "abuse", "kill", "stupid", "fraud", "password", "credit card", "urgent money"],
        }

    @property
    def version(self) -> str:
        return self.model.get("version", "unknown")

    def predict(self, text: str) -> dict:
        start = time.perf_counter()
        clean_text = text.lower().strip()
        tokens = [tok.strip(".,!?;:()[]{}\"'").lower() for tok in clean_text.split() if tok.strip()]
        labels = self.model.get("labels", ["clean", "risky"])
        scores: dict[str, float] = {}
        for label in labels:
            prior = max(float(self.model.get("priors", {}).get(label, 0.5)), 1e-9)
            score = math.log(prior)
            probs = self.model.get("token_log_probs", {}).get(label, {})
            unknown = float(self.model.get("unknown_log_probs", {}).get(label, math.log(1e-5)))
            for tok in tokens:
                score += float(probs.get(tok, unknown))
            scores[label] = score
        risky = scores.get("risky", -10.0)
        clean = scores.get("clean", -10.0)
        prob_risky = 1.0 / (1.0 + math.exp(min(max(clean - risky, -50), 50)))
        for phrase in self.model.get("risk_keywords", []):
            if phrase in clean_text:
                prob_risky = max(prob_risky, 0.72)
        label = "risky" if prob_risky >= 0.7 else "review" if prob_risky >= 0.45 else "clean"
        latency_ms = (time.perf_counter() - start) * 1000
        ML_PREDICTIONS.labels(label=label, model_version=self.version).inc()
        ML_LATENCY.observe(latency_ms / 1000)
        return {"score": round(float(prob_risky), 4), "label": label, "model_version": self.version, "latency_ms": round(latency_ms, 3)}

risk_scorer = NaiveBayesRiskScorer()
