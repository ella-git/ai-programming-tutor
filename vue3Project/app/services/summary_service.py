from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.database.database import SessionLocal
from app.database.models import Message
from app.llm.model import create_llm, MEMORY_MODEL

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一名协作编程学习总结助手。请根据下面聊天记录总结小组状态。\n\n"
     "总结内容：\n"
     "1. 当前正在完成的任务\n"
     "2. 已经解决的问题\n"
     "3. 当前未解决的问题\n"
     "4. 成员贡献情况\n"
     "5. 下一步建议\n\n"
     "要求：不要编造。不要输出代码。"),
    ("human", "{messages}"),
])


def summarize_room_messages(room_id: int) -> str:
    db = SessionLocal()
    try:
        messages = (
            db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.created_at.desc())
            .limit(100)
            .all()
        )
        messages.reverse()

        if not messages:
            return "该房间暂无聊天记录。"

        lines = [f"[{m.sender}] {m.content}" for m in messages]
        text = "\n".join(lines)

        llm = create_llm(model=MEMORY_MODEL, temperature=0.3)
        chain = SUMMARY_PROMPT | llm | StrOutputParser()
        summary = chain.invoke({"messages": text})
        return summary
    finally:
        db.close()
