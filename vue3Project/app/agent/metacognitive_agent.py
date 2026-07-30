from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.database.database import SessionLocal
from app.database.models import Message, RoomMemory, Prompt
from app.llm.model import get_llm


def get_metacognitive_prompt():
    db = SessionLocal()
    try:
        record = db.query(Prompt).filter(Prompt.agent_type == "metacognitive").first()
        if record and record.prompt:
            return ChatPromptTemplate.from_messages([
                ("system", record.prompt),
            ])
    finally:
        db.close()
    return ChatPromptTemplate.from_messages([
        ("system", "你是一名元认知智能体。你的任务：分析编程讨论房间的讨论情况。\n"
         "1. 分析讨论进度和协作情况\n"
         "2. 识别讨论中的关键观点和分歧\n"
         "3. 评估学生对问题的理解程度\n"
         "4. 提出改进讨论的建议\n\n"
         "上下文：\n"
         "聊天室长期记忆：{memory}\n"
         "最近聊天记录：{history}\n"
         "分析问题：{question}"),
    ])


def chat_with_metacognitive_agent(room_id: int, question: str) -> str:
    db = SessionLocal()
    try:
        memory_record = db.query(RoomMemory).filter(RoomMemory.room_id == room_id).first()
        memory = memory_record.summary if memory_record else "暂无长期记忆"

        recent = (
            db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.created_at.desc())
            .limit(50)
            .all()
        )
        recent.reverse()
        history_lines = [f"[{m.sender}] {m.content}" for m in recent]
        history = "\n".join(history_lines) if history_lines else "暂无聊天记录"

        llm = get_llm()
        prompt = get_metacognitive_prompt()
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({
            "memory": memory,
            "history": history,
            "question": question,
        })
        return answer
    finally:
        db.close()
