# Runtime evidence

This folder contains a reproducible local run of the checked-in chat-risk model.
Run it from the repository root:

```bash
python scripts/generate_runtime_evidence.py
```

The command reads `mlops/data/chat_risk_samples.csv`, loads
`mlops/models/current/risk_model.json`, performs one real inference per input,
and writes:

- `risk-model-trace.csv` — one measured prediction per sample;
- `risk-model-runtime.mp4` — an animation rendered from those measured results;
- `risk-model-runtime-poster.jpg` — the first decoded video frame;
- `summary.json` — model version, counts, latency, video metadata, and SHA-256 hashes.

The evidence demonstrates local `nb-risk-v1` inference and its visual trace. It
does not claim that PostgreSQL, Redis, or the live WebSocket gateway ran here;
those services require the Docker Compose stack and were unavailable on the
validation host. Use the repository load-test commands only against a running
stack when making deployment or concurrency claims.
