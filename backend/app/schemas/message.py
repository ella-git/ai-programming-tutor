from pydantic import BaseModel


class MessageHistoryItem(BaseModel):
    username: str
    content: str
    message_type: str
    created_time: str


class MessageCountResponse(BaseModel):
    count: int


class MessageClearResponse(BaseModel):
    deleted_count: int
