import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-flash-250715")
MEMORY_MODEL = os.getenv("MEMORY_MODEL", "doubao-seed-1-8-251228")
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/"

llm = ChatOpenAI(
    model=DOUBAO_MODEL,
    api_key=DOUBAO_API_KEY,
    base_url=DOUBAO_BASE_URL,
    temperature=0.7,
    max_tokens=2048,
)


def get_llm() -> ChatOpenAI:
    return llm


def create_llm(model: str = None, temperature: float = 0.5, max_tokens: int = 2048) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or DOUBAO_MODEL,
        api_key=DOUBAO_API_KEY,
        base_url=DOUBAO_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )
