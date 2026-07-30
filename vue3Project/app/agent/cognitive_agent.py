from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.database.database import SessionLocal
from app.database.models import Message, RoomMemory, Prompt
from app.llm.model import get_llm
from app.agent.prompts import AGENT_PROMPT


def get_agent_prompt(agent_type: str = "cognitive"):
    db = SessionLocal()
    try:
        record = db.query(Prompt).filter(Prompt.agent_type == agent_type).first()
        if record and record.prompt:
            return ChatPromptTemplate.from_messages([
                ("system", record.prompt),
            ])
    finally:
        db.close()
    return AGENT_PROMPT


def chat_with_cognitive_agent(room_id: int, question: str) -> str:
    db = SessionLocal()
    try:
        memory_record = db.query(RoomMemory).filter(RoomMemory.room_id == room_id).first()
        memory = memory_record.summary if memory_record else "暂无长期记忆"

        recent = (
            db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.created_at.desc())
            .limit(20)
            .all()
        )
        recent.reverse()
        history_lines = [f"[{m.sender}] {m.content}" for m in recent]
        history = "\n".join(history_lines) if history_lines else "暂无聊天记录"

        llm = get_llm()
        prompt = get_agent_prompt()
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({
            "memory": memory,
            "history": history,
            "question": question,
        })
        return answer
    finally:
        db.close()
