# Model Card: Chat Risk Naive Bayes v1

## Purpose
A lightweight, reproducible message risk model for this portfolio project. It scores messages for spam, abuse, credential-harvesting language, or threat-like content.

## Training
```bash
python mlops/training/train_risk_model.py --data mlops/data/chat_risk_samples.csv --out mlops/models/current/risk_model.json
```

## Evaluation
```bash
python mlops/evaluation/evaluate_risk_model.py
```

## Integration
The FastAPI backend loads `mlops/models/current/risk_model.json`. Every WebSocket `message.send` event receives a risk score, and the score is persisted in `messages` and `message_risk_scores`.

## Limitations
This is not a production safety classifier. It is a real, runnable MLOps integration designed to demonstrate the pipeline, model versioning, inference metrics, and admin review workflow.
