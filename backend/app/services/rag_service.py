import logging

from sqlalchemy.orm import Session

from app.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)


def get_rag_context(question: str, db: Session) -> str:
    chunks = retrieve_context(question, db, top_k=5)
    if not chunks:
        logger.info("get_rag_context: no chunks, returning empty")
        return ""
    lines = ["参考知识："]
    for i, c in enumerate(chunks, 1):
        lines.append(f"{i}. {c['content']}")
    result = "\n".join(lines)
    logger.info("get_rag_context: context len=%d chars", len(result))
    return result
