from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from sqlalchemy.orm import Session

from app.core.config import METACOGNITIVE_MODEL
from app.database.models import AgentPrompt, Message
from app.llm.model import get_chat_llm
from app.services.memory_service import MemoryService

AGENT_TYPE = "metacognitive"


def _get_system_prompt(db: Session) -> str:
    record = db.query(AgentPrompt).filter(AgentPrompt.agent_type == AGENT_TYPE).first()
    return record.prompt_content if record else "你是一名协作过程分析智能体。"


def chat_with_metacognitive_agent(db: Session, room_id: int, question: str) -> str:
    system_prompt = _get_system_prompt(db)

    memory_service = MemoryService(db)
    memory = memory_service.get_room_memory(room_id)
    memory_text = memory.summary if memory else "暂无长期记忆"

    recent_messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_time.desc())
        .limit(50)
        .all()
    )
    recent_messages.reverse()
    history_lines = [
        f"[{msg.username}] {msg.content}" for msg in recent_messages
    ]
    history_text = "\n".join(history_lines) if history_lines else "暂无聊天记录"

    template = PromptTemplate(
        input_variables=["memory", "history", "question"],
        template=(
            "上下文：\n"
            "聊天室长期记忆：{memory}\n\n"
            "最近聊天记录：\n{history}\n\n"
            "学生问题：{question}"
        ),
    )
    prompt = template.format(
        memory=memory_text,
        history=history_text,
        question=question,
    )

    llm = get_chat_llm(model=METACOGNITIVE_MODEL)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return response.content
