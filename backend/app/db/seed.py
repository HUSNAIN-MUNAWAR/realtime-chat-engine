from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models import User, Workspace, Room, RoomMembership
from app.security.passwords import hash_password

async def seed_demo_data(session: AsyncSession) -> None:
    if not settings.seed_demo_data:
        return
    if await session.scalar(select(User).where(User.email == settings.admin_email)):
        return
    admin = User(email=settings.admin_email, username="admin", hashed_password=hash_password(settings.admin_password), role="admin")
    husnain = User(email="husnain@example.com", username="husnain", hashed_password=hash_password("User12345!"), role="user")
    sara = User(email="sara@example.com", username="sara", hashed_password=hash_password("User12345!"), role="user")
    session.add_all([admin, husnain, sara])
    await session.flush()
    ws = Workspace(name="Realtime Systems Lab", slug="realtime-systems-lab", owner_id=admin.id)
    session.add(ws); await session.flush()
    rooms = [
        Room(workspace_id=ws.id, name="general", room_type="channel", created_by_id=admin.id),
        Room(workspace_id=ws.id, name="backend-scaling", room_type="channel", created_by_id=admin.id),
        Room(workspace_id=ws.id, name="incident-room", room_type="channel", created_by_id=admin.id),
    ]
    session.add_all(rooms); await session.flush()
    for user in [admin, husnain, sara]:
        for room in rooms:
            session.add(RoomMembership(room_id=room.id, user_id=user.id, role="owner" if user.id == admin.id else "member"))
    await session.commit()
