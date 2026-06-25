SHELL := /bin/bash
.PHONY: up down logs test backend-test frontend-test load-test-small load-test-1k load-test-10k train-model screenshots fmt

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f backend frontend postgres redis

test:
	docker compose run --rm backend pytest -q
	docker compose run --rm frontend npm test

backend-test:
	docker compose run --rm backend pytest -q
	docker compose run --rm frontend npm test

frontend-test:
	docker compose run --rm frontend npm test

train-model:
	docker compose run --rm backend python /app/mlops/training/train_risk_model.py --data /app/mlops/data/chat_risk_samples.csv --out /app/mlops/models/current/risk_model.json

load-test-small:
	python load_tests/ws_load_test.py --base-url http://localhost:8000 --ws-url ws://localhost:8000/ws --users 100 --rooms 10 --message-rate 1 --ramp-up 20 --duration 60 --auth-mode provision

load-test-1k:
	python load_tests/ws_load_test.py --base-url http://localhost:8000 --ws-url ws://localhost:8000/ws --users 1000 --rooms 100 --message-rate 0.2 --ramp-up 120 --duration 180 --auth-mode provision

load-test-10k:
	python load_tests/ws_load_test.py --base-url http://localhost:8000 --ws-url ws://localhost:8000/ws --users 10000 --rooms 1000 --message-rate 0.05 --ramp-up 600 --duration 300 --auth-mode provision

screenshots:
	cd frontend && npm run screenshots

fmt:
	python -m compileall backend/app load_tests mlops/training
