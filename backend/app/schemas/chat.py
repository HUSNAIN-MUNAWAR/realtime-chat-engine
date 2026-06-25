from pydantic import BaseModel, Field

class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=140)

class RoomCreate(BaseModel):
    workspace_id: str
    name: str = Field(min_length=1, max_length=120)
    room_type: str = "channel"

class DirectConversationCreate(BaseModel):
    workspace_id: str
    other_user_id: str

class RiskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)

class ProvisionLoadTestRequest(BaseModel):
    users: int = Field(ge=1, le=100000)
    rooms: int = Field(ge=1, le=10000)
    message_rate: float = Field(ge=0, le=1000)
    run_name: str = "local-load-test"
