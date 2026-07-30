from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import Message


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    def save_message(
        self, room_id: int, user_id: int, username: str, content: str, message_type: str = "text"
    ) -> Message:
        msg = Message(
            room_id=room_id,
            user_id=user_id,
            username=username,
            content=content,
            message_type=message_type,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, room_id: int) -> list[Message]:
        return (
            self.db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.created_time.asc())
            .all()
        )

    def get_message_count(self, room_id: int) -> int:
        return self.db.query(Message).filter(Message.room_id == room_id).count()

    def clear_messages_by_room(self, room_id: int) -> int:
        deleted = self.db.query(Message).filter(Message.room_id == room_id).delete()
        self.db.commit()
        return deleted
