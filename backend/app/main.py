from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.seed import seed_demo_data
from app.db.session import AsyncSessionLocal
from app.observability.metrics import metrics_endpoint
from app.realtime.manager import redis_listener
from app.realtime.ws import router as ws_router, set_redis
from app.services.redis import close_redis, init_redis

configure_logging()
stop_event = asyncio.Event()
listener_task: asyncio.Task | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global listener_task
    redis = await init_redis()
    set_redis(redis)
    async with AsyncSessionLocal() as session:
        await seed_demo_data(session)
    listener_task = asyncio.create_task(redis_listener(redis, stop_event))
    yield
    stop_event.set()
    if listener_task:
        listener_task.cancel()
    await close_redis()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.backend_cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(ws_router)
app.add_route("/metrics", metrics_endpoint, methods=["GET"])

@app.get("/health")
async def root_health():
    return {"status": "ok", "service": settings.app_name}
