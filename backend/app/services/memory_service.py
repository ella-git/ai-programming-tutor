from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import RoomMemory


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_room_memory(self, room_id: int) -> RoomMemory | None:
        return (
            self.db.query(RoomMemory)
            .filter(RoomMemory.room_id == room_id)
            .first()
        )

    def update_room_memory(self, room_id: int, summary: str) -> RoomMemory:
        memory = self.get_room_memory(room_id)
        if memory:
            memory.summary = summary
            memory.updated_time = datetime.now(timezone.utc)
        else:
            memory = RoomMemory(room_id=room_id, summary=summary)
            self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory
