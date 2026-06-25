from __future__ import annotations
import argparse, asyncio, json, random, time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4
import aiohttp, psutil, websockets

@dataclass
class Metrics:
    connected: int = 0
    failed_connections: int = 0
    sent: int = 0
    received: int = 0
    dropped: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def report(self, duration: float, args) -> dict:
        lat = sorted(self.latencies_ms)
        def pct(p: float) -> float:
            if not lat: return 0.0
            return round(lat[min(int(len(lat) * p), len(lat)-1)], 2)
        return {
            "users_requested": args.users, "rooms_requested": args.rooms,
            "message_rate_per_user": args.message_rate, "ramp_up_seconds": args.ramp_up,
            "duration_seconds": args.duration, "connected_users": self.connected,
            "failed_connections": self.failed_connections, "messages_sent": self.sent,
            "messages_received": self.received,
            "messages_sent_per_sec": round(self.sent / max(duration, 1), 2),
            "messages_received_per_sec": round(self.received / max(duration, 1), 2),
            "dropped_messages": self.dropped,
            "p50_latency_ms": pct(0.50), "p95_latency_ms": pct(0.95), "p99_latency_ms": pct(0.99),
            "client_cpu_percent": psutil.cpu_percent(interval=None),
            "client_memory_percent": psutil.virtual_memory().percent,
            "error_samples": self.errors[:20],
            "notes": "Client-side load-test report. Use Prometheus/Grafana for server CPU, memory, Redis, DB, and app metrics.",
        }

async def provision(args) -> tuple[list[dict], list[dict]]:
    async with aiohttp.ClientSession() as session:
        payload = {"users": args.users, "rooms": args.rooms, "message_rate": args.message_rate, "run_name": args.run_name}
        async with session.post(f"{args.base_url}/api/v1/load-tests/provision", json=payload, headers={"X-Load-Test-Secret": args.load_test_secret}, timeout=900) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Provision failed {resp.status}: {await resp.text()}")
            data = await resp.json()
            return data["users"], data["rooms"]

async def api_auth_users(args) -> tuple[list[dict], list[dict]]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{args.base_url}/api/v1/auth/login", json={"email":"admin@example.com","password":"Admin12345!"}) as resp:
            admin = await resp.json()
        headers = {"Authorization": f"Bearer {admin['access_token']}"}
        async with session.get(f"{args.base_url}/api/v1/workspaces", headers=headers) as resp:
            workspaces = await resp.json()
        workspace_id = workspaces[0]["id"]
        rooms = []
        for i in range(args.rooms):
            async with session.post(f"{args.base_url}/api/v1/rooms", json={"workspace_id": workspace_id, "name": f"api-lt-{uuid4().hex[:8]}-{i}", "room_type": "channel"}, headers=headers) as resp:
                rooms.append(await resp.json())
        users = []
        for i in range(args.users):
            email = f"api-lt-{uuid4().hex}-{i}@example.com"
            payload = {"email": email, "username": f"api_lt_{uuid4().hex[:12]}", "password": "LoadTest12345!"}
            async with session.post(f"{args.base_url}/api/v1/auth/register", json=payload) as resp:
                data = await resp.json()
            room = rooms[i % len(rooms)]
            await session.post(f"{args.base_url}/api/v1/rooms/{room['id']}/join", headers={"Authorization": f"Bearer {data['access_token']}"})
            users.append({"id": data["user"]["id"], "username": data["user"]["username"], "token": data["access_token"], "room_id": room["id"]})
        return users, rooms

async def virtual_user(idx: int, user: dict, args, metrics: Metrics, stop_at: float):
    await asyncio.sleep((args.ramp_up * idx) / max(args.users, 1))
    ws_url = f"{args.ws_url}?token={user['token']}"
    pending: dict[str, float] = {}
    try:
        async with websockets.connect(ws_url, max_size=2**20, ping_interval=20, ping_timeout=20) as ws:
            metrics.connected += 1
            await ws.send(json.dumps({"type": "room.join", "request_id": str(uuid4()), "payload": {"room_id": user["room_id"]}}))
            async def receiver():
                while time.time() < stop_at:
                    try: raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    except asyncio.TimeoutError: continue
                    event = json.loads(raw)
                    if event.get("type") == "message.created":
                        metrics.received += 1
                        mid = event.get("payload", {}).get("client_message_id")
                        if mid in pending:
                            metrics.latencies_ms.append((time.perf_counter() - pending.pop(mid)) * 1000)
                    elif str(event.get("type","")).startswith("error"):
                        metrics.errors.append(raw[:300])
            recv_task = asyncio.create_task(receiver())
            interval = 1.0 / args.message_rate if args.message_rate > 0 else args.duration + 1
            while time.time() < stop_at:
                client_message_id = f"lt-{idx}-{uuid4().hex}"
                pending[client_message_id] = time.perf_counter()
                payload = {"room_id": user["room_id"], "client_message_id": client_message_id, "content": f"load test msg {idx} {time.time()}"}
                await ws.send(json.dumps({"type": "message.send", "request_id": client_message_id, "payload": payload}))
                metrics.sent += 1
                await asyncio.sleep(interval * random.uniform(0.8, 1.2))
            await recv_task
            metrics.dropped += len(pending)
    except Exception as exc:
        metrics.failed_connections += 1
        if len(metrics.errors) < 20:
            metrics.errors.append(f"user {idx}: {type(exc).__name__}: {exc}")

async def run(args):
    if args.users > 10000 and not args.force_single_process:
        print("Refusing >10k sockets in one process without --force-single-process. Use --shards for the 100k distributed profile.")
        return 2
    users, rooms = await (provision(args) if args.auth_mode == "provision" else api_auth_users(args))
    if args.shards > 1:
        users = [u for i, u in enumerate(users) if i % args.shards == args.shard_index]
    args.users = len(users)
    metrics = Metrics()
    start = time.time(); stop_at = start + args.duration
    await asyncio.gather(*[asyncio.create_task(virtual_user(i, user, args, metrics, stop_at)) for i, user in enumerate(users)])
    report = metrics.report(time.time() - start, args)
    out_dir = Path(args.report_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = out_dir / f"ws-load-report-{stamp}.json"
    md_path = out_dir / f"ws-load-report-{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text("# WebSocket Load Test Report\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Reports written to {json_path} and {md_path}")
    return 0

def parse_args():
    p = argparse.ArgumentParser(description="Configurable WebSocket load tester for the chat engine")
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--ws-url", default="ws://localhost:8000/ws")
    p.add_argument("--users", type=int, required=True)
    p.add_argument("--rooms", type=int, required=True)
    p.add_argument("--message-rate", type=float, default=1.0)
    p.add_argument("--ramp-up", type=float, default=60)
    p.add_argument("--duration", type=float, default=60)
    p.add_argument("--auth-mode", choices=["provision","api"], default="provision")
    p.add_argument("--load-test-secret", default="local-load-test-secret")
    p.add_argument("--run-name", default="ws-load-test")
    p.add_argument("--report-dir", default="load_tests/reports")
    p.add_argument("--shards", type=int, default=1)
    p.add_argument("--shard-index", type=int, default=0)
    p.add_argument("--force-single-process", action="store_true")
    return p.parse_args()

if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
