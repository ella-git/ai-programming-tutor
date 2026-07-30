from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.database.models import ChatRoom, Message, RoomMember, User


class RoomService:
    def __init__(self, db: Session):
        self.db = db

    def enter_room(self, room_code: str, user: User) -> ChatRoom:
        room = self.db.query(ChatRoom).filter(ChatRoom.room_code == room_code).first()
        if not room:
            room = ChatRoom(room_code=room_code, creator_id=user.id)
            self.db.add(room)
            self.db.commit()
            self.db.refresh(room)
        existing = (
            self.db.query(RoomMember)
            .filter(RoomMember.room_id == room.id, RoomMember.user_id == user.id)
            .first()
        )
        if not existing:
            member = RoomMember(room_id=room.id, user_id=user.id)
            self.db.add(member)
            self.db.commit()
        return room

    def get_room_member_count(self, room_id: int) -> int:
        return self.db.query(RoomMember).filter(RoomMember.room_id == room_id).count()

    def list_rooms(self) -> list[dict]:
        rooms = self.db.query(ChatRoom).all()
        result = []
        for room in rooms:
            creator = self.db.query(User).filter(User.id == room.creator_id).first()
            member_count = self.get_room_member_count(room.id)
            result.append({
                "room": room,
                "creator_name": creator.username if creator else "未知",
                "member_count": member_count,
            })
        return result

    def delete_room(self, room_id: int) -> None:
        room = self.db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not room:
            raise AppException("房间不存在", status_code=404)
        self.db.query(Message).filter(Message.room_id == room_id).delete()
        self.db.query(RoomMember).filter(RoomMember.room_id == room_id).delete()
        self.db.delete(room)
        self.db.commit()

    def get_room_members(self, room_id: int) -> list[dict]:
        room = self.db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not room:
            raise AppException("房间不存在", status_code=404)
        members = (
            self.db.query(RoomMember)
            .filter(RoomMember.room_id == room_id)
            .all()
        )
        result = []
        for m in members:
            user = self.db.query(User).filter(User.id == m.user_id).first()
            result.append({
                "username": user.username if user else "未知",
                "is_online": m.is_online,
            })
        return result
