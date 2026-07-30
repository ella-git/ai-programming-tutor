from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.schemas.room import RoomDeleteResponse, RoomEnterRequest, RoomInfo, RoomListItem, RoomMemberInfo
from app.services.room_service import RoomService

router = APIRouter(prefix="/api/room", tags=["房间"])


@router.post("/enter", response_model=RoomInfo)
def enter_room(
    body: RoomEnterRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = RoomService(db)
    room = service.enter_room(body.room_code, user)
    member_count = service.get_room_member_count(room.id)
    return RoomInfo(room_id=room.id, room_code=room.room_code, member_count=member_count)


@router.get("/list", response_model=list[RoomListItem])
def list_rooms(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = RoomService(db)
    data = service.list_rooms()
    return [
        RoomListItem(
            room_id=item["room"].id,
            room_code=item["room"].room_code,
            creator_id=item["room"].creator_id,
            creator_name=item["creator_name"],
            member_count=item["member_count"],
            status=item["room"].status,
            created_time=item["room"].created_time.isoformat(),
        )
        for item in data
    ]


@router.get("/{room_id}/members", response_model=list[RoomMemberInfo])
def list_members(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = RoomService(db)
    data = service.get_room_members(room_id)
    return [
        RoomMemberInfo(username=item["username"], is_online=item["is_online"])
        for item in data
    ]


@router.delete("/{room_id}", response_model=RoomDeleteResponse)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = RoomService(db)
    service.delete_room(room_id)
    return RoomDeleteResponse(message="房间已删除")
