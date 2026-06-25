from pydantic import BaseModel, Field

class ClientEvent(BaseModel):
    type: str
    request_id: str | None = None
    payload: dict = Field(default_factory=dict)
