# Load Testing

The load tester creates real WebSocket connections, joins rooms, sends real `message.send` events, receives `message.created`, and measures client-observed latency.

## Local profiles

```bash
make load-test-small
make load-test-1k
make load-test-10k
```

## 100k distributed profile

100k WebSocket connections generally cannot be generated from one laptop because of file descriptor limits, ephemeral ports, CPU, memory, and network constraints. The script supports 100k as a distributed simulation by sharding users across multiple load-generator processes/hosts:

```bash
python load_tests/ws_load_test.py \
  --users 100000 \
  --rooms 1000 \
  --message-rate 1 \
  --ramp-up 600 \
  --duration 600 \
  --auth-mode provision \
  --shards 20 \
  --shard-index 0
```

Run `--shard-index 0..19` across 20 machines or containers.

## Report output

Reports are written to:

```text
load_tests/reports/ws-load-report-<timestamp>.json
load_tests/reports/ws-load-report-<timestamp>.md
```

The report includes connected users, failed connections, sent/received throughput, p50/p95/p99 latency, dropped messages, and client CPU/memory.

## What the report does not fake

The repository does not include invented benchmark numbers. You must run the load test on your hardware and publish the generated report if you want benchmark claims.
