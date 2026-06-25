# Benchmark Report Template

This project intentionally does not ship fake benchmark numbers. After running a load test, paste the generated report from `load_tests/reports/` here or link it from your GitHub README.

## Environment

- Date:
- Machine / cloud instance:
- OS:
- CPU:
- RAM:
- Network:
- Backend replicas:
- PostgreSQL version:
- Redis version:
- Load generator shards:

## Command

```bash
python load_tests/ws_load_test.py --users ... --rooms ... --message-rate ... --ramp-up ... --duration ...
```

## Results

| Metric | Value |
|---|---:|
| Connected users |  |
| Failed connections |  |
| Messages sent/sec |  |
| Messages received/sec |  |
| p50 ack latency |  |
| p95 ack latency |  |
| p99 ack latency |  |
| Dropped messages |  |
| Server CPU |  |
| Server memory |  |

## Notes

- Include Prometheus/Grafana screenshots generated during the same run.
- Do not compare runs unless hardware, config, user count, and message rate are listed.
