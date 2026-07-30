from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, dict[int, WebSocket]] = {}

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][user_id] = websocket

    def disconnect(self, room_id: int, user_id: int):
        if room_id in self.rooms:
            self.rooms[room_id].pop(user_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: int, message: dict, exclude_user_id: int | None = None):
        if room_id not in self.rooms:
            return
        for uid, ws in list(self.rooms[room_id].items()):
            if uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def get_online_count(self, room_id: int) -> int:
        return len(self.rooms.get(room_id, {}))


manager = ConnectionManager()
