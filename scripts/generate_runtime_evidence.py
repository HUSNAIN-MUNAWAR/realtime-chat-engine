"""Run the checked-in risk model and render an auditable local trace.

This is deliberately a model/runtime evidence script, not a substitute for a
PostgreSQL + Redis integration or a WebSocket load test.  Every prediction in
the trace is produced by the checked-in model artifact from the checked-in
CSV, and the MP4 is only a visual rendering of those measured predictions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ml.risk_model import NaiveBayesRiskScorer  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_samples(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_trace(
    samples: list[dict[str, str]], scorer: NaiveBayesRiskScorer
) -> list[dict]:
    trace: list[dict] = []
    for sequence, sample in enumerate(samples, start=1):
        started = time.perf_counter()
        prediction = scorer.predict(sample["text"])
        measured_ms = (time.perf_counter() - started) * 1000
        trace.append(
            {
                "sequence": sequence,
                "text": sample["text"],
                "expected_label": sample["label"],
                "predicted_label": prediction["label"],
                "score": prediction["score"],
                "model_version": prediction["model_version"],
                "model_reported_latency_ms": prediction["latency_ms"],
                "measured_latency_ms": round(measured_ms, 3),
            }
        )
    return trace


def wrap_text(text: str, width: int = 58) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


def render_video(trace: list[dict], output: Path) -> tuple[int, int, float]:
    width, height, fps = 1280, 720, 2.0
    writer = cv2.VideoWriter(
        str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {output}")
    for row in trace:
        frame = np.full((height, width, 3), (18, 24, 38), dtype=np.uint8)
        cv2.putText(
            frame,
            "REALTIME CHAT ENGINE | LOCAL MODEL TRACE",
            (52, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.05,
            (228, 236, 248),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"sample {row['sequence']} / {len(trace)}",
            (53, 112),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (150, 170, 198),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"model: {row['model_version']}",
            (870, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (140, 210, 180),
            2,
            cv2.LINE_AA,
        )
        cv2.rectangle(frame, (52, 160), (1228, 330), (35, 46, 68), -1)
        cv2.putText(
            frame,
            "input message",
            (78, 205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (150, 170, 198),
            2,
            cv2.LINE_AA,
        )
        for index, line in enumerate(wrap_text(row["text"]), start=1):
            cv2.putText(
                frame,
                line,
                (78, 250 + 42 * (index - 1)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.92,
                (240, 244, 250),
                2,
                cv2.LINE_AA,
            )
        score = float(row["score"])
        color = (
            (64, 210, 120)
            if score < 0.45
            else (40, 190, 230)
            if score < 0.7
            else (60, 80, 235)
        )
        cv2.putText(
            frame,
            "risk probability",
            (80, 420),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            (150, 170, 198),
            2,
            cv2.LINE_AA,
        )
        cv2.rectangle(frame, (80, 450), (900, 500), (55, 65, 85), -1)
        cv2.rectangle(frame, (80, 450), (80 + int(820 * score), 500), color, -1)
        cv2.putText(
            frame,
            f"{score:.4f}",
            (930, 489),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            color,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"prediction: {row['predicted_label'].upper()}",
            (80, 590),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.15,
            color,
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"expected: {row['expected_label']}  |  measured inference: {row['measured_latency_ms']:.3f} ms",
            (80, 640),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            (180, 190, 205),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)
    writer.release()
    return width, height, fps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, default=REPO_ROOT / "mlops/data/chat_risk_samples.csv"
    )
    parser.add_argument(
        "--model", type=Path, default=REPO_ROOT / "mlops/models/current/risk_model.json"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=REPO_ROOT / "docs/runtime_evidence"
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    samples = load_samples(args.data)
    scorer = NaiveBayesRiskScorer(str(args.model))
    trace = run_trace(samples, scorer)
    trace_path = args.output_dir / "risk-model-trace.csv"
    with trace_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trace[0]))
        writer.writeheader()
        writer.writerows(trace)

    video_path = args.output_dir / "risk-model-runtime.mp4"
    width, height, fps = render_video(trace, video_path)
    capture = cv2.VideoCapture(str(video_path))
    decoded_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    poster_path = args.output_dir / "risk-model-runtime-poster.jpg"
    cap = cv2.VideoCapture(str(video_path))
    ok, poster = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Could not decode the first evidence frame")
    cv2.imwrite(str(poster_path), poster)

    correct = sum(row["expected_label"] == row["predicted_label"] for row in trace)
    summary = {
        "status": "completed",
        "model_version": scorer.version,
        "model_path": str(args.model.relative_to(REPO_ROOT)),
        "input_path": str(args.data.relative_to(REPO_ROOT)),
        "samples": len(trace),
        "exact_label_matches": correct,
        "sample_accuracy": round(correct / len(trace), 4) if trace else 0,
        "mean_measured_latency_ms": round(
            sum(row["measured_latency_ms"] for row in trace) / len(trace), 3
        ),
        "video": {
            "width": width,
            "height": height,
            "fps": fps,
            "decoded_frames": decoded_frames,
        },
        "claim_boundary": "This proves local model inference and an evidence rendering. It does not claim a live PostgreSQL/Redis/WebSocket deployment because those services were unavailable on the validation host.",
        "artifacts": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (trace_path, video_path, poster_path)
        },
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
