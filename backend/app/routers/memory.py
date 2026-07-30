from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/memory", tags=["记忆"])


class MemoryResponse(BaseModel):
    room_id: int
    summary: str


class MemoryUpdateRequest(BaseModel):
    room_id: int
    summary: str


@router.get("/{room_id}", response_model=MemoryResponse)
def get_memory(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = MemoryService(db)
    memory = service.get_room_memory(room_id)
    return MemoryResponse(
        room_id=room_id,
        summary=memory.summary if memory else "",
    )


@router.post("/update", response_model=MemoryResponse)
def update_memory(
    body: MemoryUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = MemoryService(db)
    memory = service.update_room_memory(body.room_id, body.summary)
    return MemoryResponse(room_id=memory.room_id, summary=memory.summary)
