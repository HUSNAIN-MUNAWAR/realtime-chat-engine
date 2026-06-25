from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))
from app.ml.risk_model import NaiveBayesRiskScorer

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("mlops/data/chat_risk_samples.csv"))
    parser.add_argument("--model", type=Path, default=Path("mlops/models/current/risk_model.json"))
    parser.add_argument("--out", type=Path, default=Path("mlops/reports/evaluation.json"))
    args = parser.parse_args()
    scorer = NaiveBayesRiskScorer(str(args.model))
    total = correct = 0
    confusion = {"clean": {"clean": 0, "risky": 0}, "risky": {"clean": 0, "risky": 0}}
    with args.data.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pred = scorer.predict(row["text"])
            pred_binary = "risky" if pred["score"] >= 0.5 else "clean"
            truth = row["label"]
            confusion.setdefault(truth, {}).setdefault(pred_binary, 0)
            confusion[truth][pred_binary] += 1
            total += 1
            correct += int(pred_binary == truth)
    report = {"model_version": scorer.version, "rows": total, "accuracy_on_sample": correct / total if total else 0, "confusion": confusion}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
