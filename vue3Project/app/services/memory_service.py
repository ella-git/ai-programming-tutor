from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import RoomMemory


def get_room_memory(room_id: int, db: Session):
    return db.query(RoomMemory).filter(RoomMemory.room_id == room_id).first()


def update_room_memory(room_id: int, summary: str, db: Session):
    memory = db.query(RoomMemory).filter(RoomMemory.room_id == room_id).first()
    if memory:
        memory.summary = summary
        memory.updated_time = datetime.utcnow()
    else:
        memory = RoomMemory(room_id=room_id, summary=summary, updated_time=datetime.utcnow())
        db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory
