from sqlalchemy import Select, desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Message, MessageDeliveryReceipt, MessageReadReceipt, MessageRiskScore, RoomMembership

async def is_member(session: AsyncSession, room_id: str, user_id: str) -> bool:
    return bool(await session.scalar(select(RoomMembership.id).where(RoomMembership.room_id == room_id, RoomMembership.user_id == user_id)))

async def get_message_by_client_id(session: AsyncSession, sender_id: str, client_message_id: str) -> Message | None:
    return await session.scalar(select(Message).where(Message.sender_id == sender_id, Message.client_message_id == client_message_id))

async def is_room_message(session: AsyncSession, message_id: str, room_id: str) -> bool:
    """Check both message existence and room ownership before recording a receipt."""
    return bool(await session.scalar(select(Message.id).where(Message.id == message_id, Message.room_id == room_id)))

async def create_message(session: AsyncSession, room_id: str, sender_id: str, client_message_id: str, content: str, parent_message_id: str | None, risk: dict) -> Message:
    message = Message(room_id=room_id, sender_id=sender_id, client_message_id=client_message_id, content=content, parent_message_id=parent_message_id, risk_score=risk["score"], risk_label=risk["label"])
    session.add(message)
    await session.flush()
    session.add(MessageRiskScore(message_id=message.id, score=risk["score"], label=risk["label"], model_version=risk["model_version"], latency_ms=risk["latency_ms"]))
    await session.commit()
    await session.refresh(message)
    return message

async def add_delivery_receipt(session: AsyncSession, message_id: str, user_id: str) -> None:
    await session.execute(pg_insert(MessageDeliveryReceipt).values(message_id=message_id, user_id=user_id).on_conflict_do_nothing(index_elements=["message_id", "user_id"]))
    await session.commit()

async def add_read_receipt(session: AsyncSession, message_id: str, user_id: str) -> None:
    await session.execute(pg_insert(MessageReadReceipt).values(message_id=message_id, user_id=user_id).on_conflict_do_nothing(index_elements=["message_id", "user_id"]))
    await session.commit()

def message_to_event(message: Message, sender_username: str | None = None) -> dict:
    return {
        "id": message.id, "room_id": message.room_id, "sender_id": message.sender_id,
        "sender_username": sender_username, "client_message_id": message.client_message_id,
        "content": message.content, "parent_message_id": message.parent_message_id,
        "risk_score": message.risk_score, "risk_label": message.risk_label,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }

async def list_messages(session: AsyncSession, room_id: str, limit: int = 50, before: str | None = None) -> tuple[list[Message], str | None]:
    stmt: Select = select(Message).where(Message.room_id == room_id).order_by(desc(Message.created_at)).limit(limit + 1)
    if before:
        cursor = await session.get(Message, before)
        if cursor:
            stmt = stmt.where(Message.created_at < cursor.created_at)
    rows = list((await session.scalars(stmt)).all())
    next_cursor = rows[-1].id if len(rows) > limit else None
    return list(reversed(rows[:limit])), next_cursor

async def message_counts(session: AsyncSession) -> dict:
    total = await session.scalar(select(func.count(Message.id))) or 0
    risky = await session.scalar(select(func.count(Message.id)).where(Message.risk_score >= 0.7)) or 0
    return {"total_messages": total, "risky_messages": risky}
