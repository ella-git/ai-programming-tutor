from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.database.models import Prompt
from app.agent.cognitive_agent import chat_with_cognitive_agent
from app.agent.metacognitive_agent import chat_with_metacognitive_agent
from app.routers.websocket import manager, save_message

router = APIRouter()


class AgentRequest(BaseModel):
    room_id: int = 0
    question: str
    client_id: str = ""


class AgentResponse(BaseModel):
    answer: str


@router.post("/api/agent/chat", response_model=AgentResponse)
async def agent_chat(request: AgentRequest):
    answer = chat_with_cognitive_agent(request.room_id, request.question)
    save_message(request.room_id, "认知智能体", answer, "agent")
    await manager.broadcast(request.room_id, {
        "type": "agent",
        "username": "认知智能体",
        "content": answer,
        "time": datetime.utcnow().isoformat(),
        "request_id": request.client_id,
    })
    return AgentResponse(answer=answer)


@router.post("/api/agent/metacognitive/chat", response_model=AgentResponse)
async def metacognitive_chat(request: AgentRequest):
    answer = chat_with_metacognitive_agent(request.room_id, request.question)
    save_message(request.room_id, "小智同学", answer, "agent")
    await manager.broadcast(request.room_id, {
        "type": "agent",
        "agent": "metacognitive",
        "username": "小智同学",
        "content": answer,
        "time": datetime.utcnow().isoformat(),
    })
    return AgentResponse(answer=answer)


@router.get("/api/agent/prompt/{agent_type}")
def get_prompt(agent_type: str, db: Session = Depends(get_db)):
    record = db.query(Prompt).filter(Prompt.agent_type == agent_type).first()
    if not record:
        return {"filename": "", "prompt": "", "version": None, "updated_time": None}
    return {
        "filename": record.filename,
        "prompt": record.prompt,
        "version": record.version,
        "updated_time": record.updated_time.isoformat() if record.updated_time else None,
    }


@router.post("/api/agent/prompt/upload")
async def upload_prompt(agent_type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("gbk", errors="replace")

    record = db.query(Prompt).filter(Prompt.agent_type == agent_type).first()
    if record:
        record.filename = file.filename
        record.prompt = text
        record.version = (record.version or 1) + 1
        record.updated_time = datetime.utcnow()
    else:
        record = Prompt(
            agent_type=agent_type,
            filename=file.filename,
            prompt=text,
            version=1,
            updated_time=datetime.utcnow(),
        )
        db.add(record)
    db.commit()
    return {"message": "上传成功", "filename": file.filename}
