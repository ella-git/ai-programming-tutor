from pydantic import BaseModel


class RoomEnterRequest(BaseModel):
    room_code: str


class RoomInfo(BaseModel):
    room_id: int
    room_code: str
    member_count: int


class RoomListItem(BaseModel):
    room_id: int
    room_code: str
    creator_id: int
    creator_name: str
    member_count: int
    status: str
    created_time: str


class RoomMemberInfo(BaseModel):
    username: str
    is_online: bool


class RoomDeleteResponse(BaseModel):
    message: str
