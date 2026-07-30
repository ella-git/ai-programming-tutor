from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.database.models import AgentPrompt, Message
from app.llm.model import get_chat_llm
from app.services.memory_service import MemoryService

MIN_HISTORY = 20
AGENT_TYPE = "cognitive"


def _get_system_prompt(db: Session) -> str:
    record = db.query(AgentPrompt).filter(AgentPrompt.agent_type == AGENT_TYPE).first()
    return record.prompt_content if record else "你是一名编程认知智能体。"


def chat_with_cognitive_agent(db: Session, room_id: int, question: str) -> str:
    system_prompt = _get_system_prompt(db)

    memory_service = MemoryService(db)
    memory = memory_service.get_room_memory(room_id)
    memory_text = memory.summary if memory else "暂无长期记忆"

    limit = MIN_HISTORY
    if memory and memory.updated_time:
        count_since = (
            db.query(Message)
            .filter(
                Message.room_id == room_id,
                Message.created_time > memory.updated_time,
            )
            .count()
        )
        limit = max(MIN_HISTORY, count_since)

    recent_messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_time.desc())
        .limit(limit)
        .all()
    )
    recent_messages.reverse()
    history_lines = [
        f"[{msg.username}] {msg.content}" for msg in recent_messages
    ]
    history_text = "\n".join(history_lines) if history_lines else "暂无聊天记录"

    rag_context = ""
    try:
        from app.services.rag_service import get_rag_context
        rag_context = get_rag_context(question, db)
    except Exception:
        pass

    sections = [f"上下文：", f"聊天室长期记忆：{memory_text}"]
    if rag_context:
        sections.append(f"\n知识库参考（请优先根据以下参考知识回答问题）：\n{rag_context}")
    sections.append(f"\n最近聊天记录：\n{history_text}")
    sections.append(f"学生问题：{question}")
    prompt = "\n\n".join(sections)

    llm = get_chat_llm()
    system_instruction = system_prompt
    if rag_context:
        system_instruction += "\n\n当上下文中有知识库参考内容时，你必须优先根据知识库中的信息回答学生问题。如果你在知识库中找到了学生询问的信息，直接告诉学生具体内容，不要说自己没有。"
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return response.content
