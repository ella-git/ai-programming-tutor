from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database.database import Base


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), default="")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    sender = Column(String(255), default="")
    content = Column(Text, default="")
    message_type = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class RoomMemory(Base):
    __tablename__ = "room_memory"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), unique=True, nullable=False)
    summary = Column(Text, default="")
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(100), unique=True, nullable=False, index=True)
    filename = Column(String(255), default="")
    prompt = Column(Text, default="")
    version = Column(Integer, default=1)
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SemanticConfig(Base):
    __tablename__ = "semantic_config"

    id = Column(Integer, primary_key=True, index=True)
    interval_seconds = Column(Integer, default=20)


class SemanticKeyword(Base):
    __tablename__ = "semantic_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
