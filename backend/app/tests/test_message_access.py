import pytest

from app.services.message_service import is_room_message


class FakeSession:
    def __init__(self, value):
        self.value = value

    async def scalar(self, _statement):
        return self.value


@pytest.mark.asyncio
async def test_receipt_scope_requires_message_in_requested_room():
    assert await is_room_message(FakeSession("message-1"), "message-1", "room-1")
    assert not await is_room_message(FakeSession(None), "message-1", "room-2")
