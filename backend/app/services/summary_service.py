from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import MEMORY_MODEL
from app.database.database import SessionLocal
from app.database.models import Message
from app.llm.model import get_chat_llm

_SUMMARY_SYSTEM_PROMPT = """你是一名协作编程学习总结助手。

请根据下面聊天记录总结小组状态。

总结内容：
1. 当前正在完成的任务
2. 已经解决的问题
3. 当前未解决的问题
4. 成员贡献情况
5. 下一步建议

要求：
- 不要编造
- 不要输出代码
- 保持简洁"""


def summarize_room_messages(room_id: int) -> str:
    db = SessionLocal()
    try:
        messages = (
            db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.created_time.desc())
            .limit(100)
            .all()
        )
        messages.reverse()

        if not messages:
            return ""

        chat_lines = [
            f"[{msg.username}] {msg.content}" for msg in messages
        ]
        chat_text = "\n".join(chat_lines)

        llm = get_chat_llm(model=MEMORY_MODEL)
        prompt_messages = [
            SystemMessage(content=_SUMMARY_SYSTEM_PROMPT),
            HumanMessage(content=f"聊天记录：\n{chat_text}"),
        ]
        response = llm.invoke(prompt_messages)
        return response.content
    finally:
        db.close()
