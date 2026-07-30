import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-secure-random-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
KNOWLEDGE_FILES_DIR = os.path.join(BASE_DIR, "storage", "knowledge_files")
FAISS_INDEX_DIR = os.path.join(BASE_DIR, "data", "faiss")

TIMEZONE = "Asia/Shanghai"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3004",
    "http://localhost:3000",
]

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
AGENT_MODEL = os.getenv("AGENT_MODEL", "doubao-seed-1-6-flash-250715")
MEMORY_MODEL = os.getenv("MEMORY_MODEL", "glm-4-7-251222")
METACOGNITIVE_MODEL = os.getenv("METACOGNITIVE_MODEL", "deepseek-v4-pro-260425")
