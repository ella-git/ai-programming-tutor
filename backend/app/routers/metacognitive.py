import asyncio
import sys
import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.services.message_service import MessageService
from app.websocket.manager import manager

router = APIRouter(prefix="/api/agent/metacognitive", tags=["元认知智能体"])


class MetaCognitiveRequest(BaseModel):
    room_id: int
    question: str
    client_id: str = ""


class MetaCognitiveResponse(BaseModel):
    success: bool
    answer: str = ""


def _run_agent(room_id: int, question: str) -> str:
    from app.database.database import SessionLocal

    db = SessionLocal()
    try:
        from app.agents.metacognitive_agent import chat_with_metacognitive_agent
        return chat_with_metacognitive_agent(db, room_id, question)
    finally:
        db.close()


@router.post("/chat", response_model=MetaCognitiveResponse)
async def metacognitive_chat(
    body: MetaCognitiveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sys.stderr.flush()

    request_id = body.client_id or str(int(datetime.now(timezone.utc).timestamp()))

    try:
        msg_service = MessageService(db)
        now = datetime.now(timezone.utc).isoformat()

        question = f"@元认知智能体 {body.question}"
        msg_service.save_message(body.room_id, user.id, user.username, question, "text")
        await manager.broadcast(
            body.room_id,
            {
                "type": "message",
                "username": user.username,
                "content": question,
                "time": now,
            },
        )

        await manager.broadcast(
            body.room_id,
            {
                "type": "agent_pending",
                "username": user.username,
                "request_id": request_id,
                "time": now,
            },
        )

        agent_answer = await asyncio.to_thread(_run_agent, body.room_id, body.question)
        print(f"[metacognitive] answer length={len(agent_answer)}", file=sys.stderr)

        reply = f"@{user.username} {agent_answer}"
        msg_service.save_message(body.room_id, user.id, "元认知智能体", reply, "agent")

        await manager.broadcast(
            body.room_id,
            {
                "type": "agent",
                "agent": "metacognitive",
                "request_id": request_id,
                "username": "元认知智能体",
                "content": reply,
                "time": datetime.now(timezone.utc).isoformat(),
            },
        )

        return MetaCognitiveResponse(success=True, answer=agent_answer)
    except Exception:
        traceback.print_exc()
        print("[metacognitive] FAILED", file=sys.stderr)
        sys.stderr.flush()
        try:
            if request_id:
                await manager.broadcast(
                    body.room_id,
                    {
                        "type": "agent",
                        "agent": "metacognitive",
                        "request_id": request_id,
                        "username": "元认知智能体",
                        "content": f"@{user.username} 抱歉，智能体暂时无法回答。",
                        "time": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception:
            pass
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"detail": "智能体调用失败"})
