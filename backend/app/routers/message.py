import io
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.core.config import TIMEZONE
from app.core.security import get_current_user
from app.database.database import get_db
from app.database.models import ChatRoom, User
from app.schemas.message import MessageClearResponse, MessageCountResponse, MessageHistoryItem
from app.services.message_service import MessageService

router = APIRouter(prefix="/api/messages", tags=["消息"])


@router.get("/{room_id}", response_model=list[MessageHistoryItem])
def get_messages(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = MessageService(db)
    messages = service.get_messages(room_id)
    return [
        MessageHistoryItem(
            username=msg.username,
            content=msg.content,
            message_type=msg.message_type,
            created_time=msg.created_time.isoformat(),
        )
        for msg in messages
    ]


@router.get("/{room_id}/count", response_model=MessageCountResponse)
def get_message_count(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = MessageService(db)
    count = service.get_message_count(room_id)
    return MessageCountResponse(count=count)


@router.delete("/{room_id}/clear", response_model=MessageClearResponse)
def clear_messages(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = MessageService(db)
    deleted = service.clear_messages_by_room(room_id)
    return MessageClearResponse(deleted_count=deleted)


@router.get("/{room_id}/export")
def export_messages(
    room_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    room_code = room.room_code if room else f"room_{room_id}"

    service = MessageService(db)
    messages = service.get_messages(room_id)

    tz = ZoneInfo(TIMEZONE)
    base_url = str(request.base_url).rstrip("/")

    wb = Workbook()
    ws = wb.active
    ws.title = f"room_{room_id}"

    ws.append(["房间名称", "发送者", "发送时间", "消息内容", "消息类型"])

    for msg in messages:
        local_time = msg.created_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content
        if msg.message_type == "image" and content.startswith("/uploads/"):
            content = f"{base_url}{content}"

        ws.append([
            room_code,
            msg.username,
            local_time,
            content,
            msg.message_type,
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{room_code}_messages.xlsx"'},
    )
