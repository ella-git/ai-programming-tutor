from pydantic import BaseModel
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Message, ChatRoom


router = APIRouter()


class EnterRoomRequest(BaseModel):
    room_code: str = ""


@router.post("/api/room/enter")
def enter_room(req: EnterRoomRequest, db: Session = Depends(get_db)):
    if not req.room_code:
        return {"error": "room_code required"}
    room = db.query(ChatRoom).filter(ChatRoom.name == req.room_code).first()
    if not room:
        room = ChatRoom(name=req.room_code)
        db.add(room)
        db.commit()
        db.refresh(room)
    return {"room_id": room.id, "name": room.name}


@router.get("/api/room/list")
def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(ChatRoom).all()
    result = []
    for r in rooms:
        msg_count = db.query(Message).filter(Message.room_id == r.id).count()
        member_set = set()
        msgs = (
            db.query(Message)
            .filter(Message.room_id == r.id, Message.message_type == "system")
            .order_by(Message.created_at)
            .all()
        )
        for m in msgs:
            if "离开" in m.content:
                name = m.content.replace("离开了聊天室", "").replace("离开聊天室", "").strip()
                member_set.discard(name)
            elif "进入" in m.content:
                name = m.content.replace("进入聊天室", "").replace("进入了聊天室", "").strip()
                member_set.add(name)
        result.append({
            "room_id": r.id,
            "room_code": r.name,
            "member_count": len(member_set),
            "message_count": msg_count,
        })
    return result


@router.get("/api/room/{room_id}/members")
def get_room_members(room_id: int, db: Session = Depends(get_db)):
    member_set = set()
    msgs = (
        db.query(Message)
        .filter(Message.room_id == room_id, Message.message_type == "system")
        .order_by(Message.created_at)
        .all()
    )
    for m in msgs:
        if "离开" in m.content:
            name = m.content.replace("离开了聊天室", "").replace("离开聊天室", "").strip()
            member_set.discard(name)
        elif "进入" in m.content:
            name = m.content.replace("进入聊天室", "").replace("进入了聊天室", "").strip()
            member_set.add(name)
    return [{"username": n} for n in member_set]


@router.delete("/api/room/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    db.query(Message).filter(Message.room_id == room_id).delete()
    db.query(ChatRoom).filter(ChatRoom.id == room_id).delete()
    db.commit()
    return {"message": "deleted"}


@router.get("/api/messages/{room_id}")
def get_room_messages(room_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at)
        .all()
    )
    return [
        {
            "id": m.id,
            "room_id": m.room_id,
            "sender": m.sender,
            "content": m.content,
            "message_type": m.message_type,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.get("/api/messages/{room_id}/count")
def get_message_count(room_id: int, db: Session = Depends(get_db)):
    count = db.query(Message).filter(Message.room_id == room_id).count()
    return {"count": count}


@router.delete("/api/messages/{room_id}/clear")
def clear_messages(room_id: int, db: Session = Depends(get_db)):
    db.query(Message).filter(Message.room_id == room_id).delete()
    db.commit()
    return {"message": "cleared"}
