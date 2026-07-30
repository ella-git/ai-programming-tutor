from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import AgentPrompt, User

router = APIRouter(prefix="/api/agent/prompt", tags=["智能体Prompt"])


@router.post("/upload")
async def upload_prompt(
    agent_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="仅支持 .txt 文件")
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请使用 UTF-8 编码的 .txt 文件")
    existing = db.query(AgentPrompt).filter(AgentPrompt.agent_type == agent_type).first()
    if existing:
        existing.prompt_content = content
        existing.filename = file.filename or existing.filename
        existing.version += 1
        existing.updated_time = datetime.now(timezone.utc)
    else:
        record = AgentPrompt(
            agent_type=agent_type,
            prompt_content=content,
            filename=file.filename or "unknown.txt",
            version=1,
        )
        db.add(record)
    db.commit()
    return {"success": True, "agent_type": agent_type}


@router.get("/{agent_type}")
def get_prompt(agent_type: str, db: Session = Depends(get_db)):
    record = db.query(AgentPrompt).filter(AgentPrompt.agent_type == agent_type).first()
    if not record:
        return {"agent_type": agent_type, "prompt": None, "filename": None, "version": None, "updated_time": None}
    return {
        "agent_type": record.agent_type,
        "prompt": record.prompt_content,
        "filename": record.filename,
        "version": record.version,
        "updated_time": record.updated_time.isoformat() if record.updated_time else None,
    }
