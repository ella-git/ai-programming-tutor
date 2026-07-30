from langchain_openai import ChatOpenAI

from app.core.config import DOUBAO_API_KEY, DOUBAO_BASE_URL, AGENT_MODEL


def get_chat_llm(model: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or AGENT_MODEL,
        api_key=DOUBAO_API_KEY,
        base_url=DOUBAO_BASE_URL,
        temperature=0.7,
    )
