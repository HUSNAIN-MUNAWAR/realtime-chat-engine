from __future__ import annotations
import argparse, csv, json, math
from collections import Counter, defaultdict
from pathlib import Path

def tokenize(text: str) -> list[str]:
    return [tok.strip(".,!?;:()[]{}\"'").lower() for tok in text.split() if tok.strip()]

def train(data_path: Path) -> dict:
    label_docs = Counter()
    token_counts = defaultdict(Counter)
    vocab = set()
    with data_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label = row["label"].strip()
            label_docs[label] += 1
            for token in tokenize(row["text"]):
                token_counts[label][token] += 1
                vocab.add(token)
    labels = sorted(label_docs)
    total_docs = sum(label_docs.values())
    priors = {label: label_docs[label] / total_docs for label in labels}
    token_log_probs, unknown_log_probs = {}, {}
    vocab_size = len(vocab)
    for label in labels:
        total_tokens = sum(token_counts[label].values())
        denom = total_tokens + vocab_size
        token_log_probs[label] = {tok: math.log((token_counts[label][tok] + 1) / denom) for tok in vocab}
        unknown_log_probs[label] = math.log(1 / denom)
    return {
        "version": "nb-risk-v1",
        "labels": labels,
        "priors": priors,
        "token_log_probs": token_log_probs,
        "unknown_log_probs": unknown_log_probs,
        "risk_keywords": ["spam", "scam", "hate", "attack", "abuse", "kill", "stupid", "fraud", "password", "credit", "urgent money"],
        "training_rows": total_docs,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    model = train(args.data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(model, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "model_version": model["version"], "out": str(args.out)}, indent=2))

if __name__ == "__main__":
    main()
