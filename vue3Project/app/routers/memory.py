from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.memory_service import get_room_memory, update_room_memory

router = APIRouter()


class UpdateMemoryRequest(BaseModel):
    room_id: int
    summary: str


@router.get("/api/memory/{room_id}")
def read_memory(room_id: int, db: Session = Depends(get_db)):
    memory = get_room_memory(room_id, db)
    if not memory:
        return {"room_id": room_id, "summary": ""}
    return {"room_id": memory.room_id, "summary": memory.summary}


@router.post("/api/memory/update")
def update_memory(request: UpdateMemoryRequest, db: Session = Depends(get_db)):
    memory = update_room_memory(request.room_id, request.summary, db)
    return {"room_id": memory.room_id, "summary": memory.summary}
