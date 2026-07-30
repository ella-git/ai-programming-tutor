import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token
from app.database.database import SessionLocal
from app.database.models import RoomMember, User
from app.semantic.trigger import run_semantic_check
from app.services.message_service import MessageService
from app.websocket.manager import manager

router = APIRouter()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: int, token: str = Query(...)):
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001)
        return

    user_id = int(payload["sub"])
    username = payload.get("username", "未知")

    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        await websocket.close(code=4004)
        return

    ws_room_id = room_id
    await manager.connect(ws_room_id, user_id, websocket)

    db.query(RoomMember).filter(
        RoomMember.room_id == ws_room_id,
        RoomMember.user_id == user_id,
    ).update({"is_online": True})
    db.commit()

    try:
        await manager.broadcast(
            ws_room_id,
            {"type": "system", "content": f"{username} 进入了房间", "time": now_iso()},
            exclude_user_id=user_id,
        )

        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type", "message")
            content = data.get("content", "")
            if not content:
                continue

            msg_service = MessageService(db)
            msg_service.save_message(room_id, user_id, username, content, msg_type)

            await manager.broadcast(
                ws_room_id,
                {"type": msg_type, "username": username, "content": content, "time": now_iso()},
            )

            if msg_type == "message":
                asyncio.ensure_future(run_semantic_check(ws_room_id, content, user_id))
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws_room_id, user_id)
        db.query(RoomMember).filter(
            RoomMember.room_id == ws_room_id,
            RoomMember.user_id == user_id,
        ).update({"is_online": False})
        db.commit()
        await manager.broadcast(
            ws_room_id,
            {"type": "system", "content": f"{username} 离开了房间", "time": now_iso()},
        )
        db.close()