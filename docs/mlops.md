# MLOps Workflow

```mermaid
flowchart LR
  DATA[Sample labeled chat data] --> TRAIN[train_risk_model.py]
  TRAIN --> MODEL[models/current/risk_model.json]
  MODEL --> API[FastAPI inference endpoint]
  API --> WS[WebSocket message.send]
  WS --> PG[(messages + message_risk_scores)]
  API --> PROM[Prometheus ML metrics]
  PG --> ADMIN[Admin risk review dashboard]
```

## Train

```bash
python mlops/training/train_risk_model.py --data mlops/data/chat_risk_samples.csv --out mlops/models/current/risk_model.json
```

## Evaluate

```bash
python mlops/evaluation/evaluate_risk_model.py
```

## Inference endpoint

```text
POST /api/v1/mlops/risk-score
```

Every persisted chat message stores `risk_score`, `risk_label`, and a row in `message_risk_scores` with model version and inference latency.
