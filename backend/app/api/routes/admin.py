from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models import LoadTestRun, Message, Room, User
from app.observability.system import system_snapshot
from app.realtime.manager import manager
from app.security.dependencies import require_admin
from app.services.message_service import message_counts

router = APIRouter()

@router.get("/stats")
async def stats(session: AsyncSession = Depends(get_session), _admin: User = Depends(require_admin)):
    users = await session.scalar(select(func.count(User.id))) or 0
    rooms = await session.scalar(select(func.count(Room.id))) or 0
    counts = await message_counts(session)
    return {"users": users, "rooms": rooms, **counts, "active_connections_local": len(manager.connections), "active_rooms_local": len(manager.room_connections), "system": system_snapshot()}

@router.get("/risky-messages")
async def risky_messages(session: AsyncSession = Depends(get_session), _admin: User = Depends(require_admin)):
    rows = (await session.scalars(select(Message).where(Message.risk_score >= 0.45).order_by(desc(Message.created_at)).limit(100))).all()
    return [{"id": m.id, "room_id": m.room_id, "sender_id": m.sender_id, "content": m.content, "risk_score": m.risk_score, "risk_label": m.risk_label, "created_at": m.created_at.isoformat() if m.created_at else None} for m in rows]

@router.get("/load-test-runs")
async def load_test_runs(session: AsyncSession = Depends(get_session), _admin: User = Depends(require_admin)):
    rows = (await session.scalars(select(LoadTestRun).order_by(desc(LoadTestRun.created_at)).limit(50))).all()
    return [{"id": r.id, "name": r.name, "users": r.users, "rooms": r.rooms, "message_rate": r.message_rate, "status": r.status, "report_path": r.report_path, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]
