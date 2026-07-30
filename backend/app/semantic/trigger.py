import asyncio
import logging
from datetime import datetime, timezone

from app.agents.metacognitive_agent import chat_with_metacognitive_agent
from app.database.database import SessionLocal
from app.semantic.detector import detect
from app.services.message_service import MessageService
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def run_semantic_check(room_id: int, message_text: str, user_id: int):
    db = SessionLocal()
    try:
        result = detect(db, message_text)
        if result is None:
            return

        keyword = result["keyword"]
        score = result["score"]

        analysis_question = (
            f"系统检测到用户消息包含关键词「{keyword}」（相似度{score:.2f}），"
            f"用户原消息：{message_text}\n"
            f"请根据聊天上下文判断是否需要干预，并给出分析。"
        )

        agent_answer = await asyncio.to_thread(
            chat_with_metacognitive_agent, db, room_id, analysis_question
        )

        msg_service = MessageService(db)
        msg_service.save_message(
            room_id, user_id, "元认知智能体", agent_answer, "agent"
        )

        now = datetime.now(timezone.utc).isoformat()
        await manager.broadcast(
            room_id,
            {
                "type": "agent",
                "agent": "metacognitive",
                "username": "元认知智能体",
                "content": agent_answer,
                "time": now,
            },
        )
        logger.info(
            "Metacognitive agent triggered by keyword=%s score=%.4f room=%d",
            keyword, score, room_id,
        )
    except Exception:
        logger.exception("Semantic trigger failed for room %d", room_id)
    finally:
        db.close()
