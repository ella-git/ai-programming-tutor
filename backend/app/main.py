import logging
import os
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles



from app.core.config import CORS_ORIGINS, FAISS_INDEX_DIR, KNOWLEDGE_FILES_DIR, UPLOAD_DIR
from app.core.exceptions import AppException
from app.database.database import Base, engine
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_embedding import KnowledgeEmbedding
from app.models.knowledge_file import KnowledgeFile
from app.models.semantic_analysis_config import SemanticAnalysisConfig
from app.models.semantic_keyword import SemanticKeyword
from app.models.semantic_keyword_embedding import SemanticKeywordEmbedding
from app.routers import agent, agent_prompt, auth, knowledge, memory, message, metacognitive, room, semantic, upload
from app.tasks.memory_summary_task import scheduler as memory_scheduler
from app.tasks.memory_summary_task import start_memory_summary_task
from app.websocket import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(KNOWLEDGE_FILES_DIR, exist_ok=True)
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    start_memory_summary_task()

    import threading
    def _warm_embeddings():
        try:
            from app.utils.embedding_model import get_embedding_model
            get_embedding_model()
            from app.semantic.detector import _embed_text
            _embed_text("预热")
        except Exception as e:
            pass
    threading.Thread(target=_warm_embeddings, daemon=True).start()

    yield
    memory_scheduler.shutdown()


app = FastAPI(
    title="AI Chat Room API",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(room.router)
app.include_router(message.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(agent_prompt.router)
app.include_router(memory.router)
app.include_router(knowledge.router)
app.include_router(metacognitive.router)
app.include_router(semantic.router)
