import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.database.database import SessionLocal
from app.database.models import Message, SemanticKeyword
from app.agent.cognitive_agent import chat_with_cognitive_agent
from app.agent.metacognitive_agent import chat_with_metacognitive_agent

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, room_id: int, ws: WebSocket):
        await ws.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(ws)

    def disconnect(self, room_id: int, ws: WebSocket):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [c for c in self.active_connections[room_id] if c != ws]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        if room_id not in self.active_connections:
            return
        for conn in self.active_connections[room_id]:
            try:
                await conn.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


def save_message(room_id: int, sender: str, content: str, message_type: str = "user"):
    db = SessionLocal()
    try:
        msg = Message(room_id=room_id, sender=sender, content=content, message_type=message_type)
        db.add(msg)
        db.commit()
    finally:
        db.close()


@router.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: int, token: str = Query(default="")):
    username = token if token else "anonymous"
    await manager.connect(room_id, ws)

    await manager.broadcast(room_id, {
        "type": "system",
        "content": f"{username} 进入聊天室",
        "time": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "message":
                content = data.get("content", "")
                save_message(room_id, username, content, "user")
                await manager.broadcast(room_id, {
                    "type": "message",
                    "username": username,
                    "content": content,
                    "time": datetime.utcnow().isoformat(),
                })

                try:
                    kw_db = SessionLocal()
                    try:
                        keywords = [k.keyword for k in kw_db.query(SemanticKeyword).all()]
                    except Exception:
                        keywords = []
                    finally:
                        kw_db.close()
                    if any(kw in content for kw in keywords):
                        answer = chat_with_metacognitive_agent(room_id, content)
                        save_message(room_id, "小智同学", answer, "agent")
                        await manager.broadcast(room_id, {
                            "type": "agent",
                            "agent": "metacognitive",
                            "username": "小智同学",
                            "content": answer,
                            "time": datetime.utcnow().isoformat(),
                        })
                except Exception:
                    pass

            elif msg_type == "agent_message":
                content = data.get("content", "")
                save_message(room_id, username, content, "user")
                answer = chat_with_cognitive_agent(room_id, content)
                save_message(room_id, "认知智能体", answer, "agent")
                await manager.broadcast(room_id, {
                    "type": "agent",
                    "username": "认知智能体",
                    "content": answer,
                    "time": datetime.utcnow().isoformat(),
                })

            elif msg_type == "image":
                content = data.get("content", "")
                save_message(room_id, username, content, "user")
                await manager.broadcast(room_id, {
                    "type": "image",
                    "username": username,
                    "content": content,
                    "time": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        manager.disconnect(room_id, ws)
        await manager.broadcast(room_id, {
            "type": "system",
            "content": f"{username} 离开聊天室",
            "time": datetime.utcnow().isoformat(),
        })
