import logging

from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.faiss_store import search
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


def retrieve_context(question: str, db: Session, top_k: int = 5):
    logger.info("retrieve_context: question=%s", question[:50])

    vector = generate_embedding(question)
    results = search(vector, top_k)

    if not results:
        logger.warning("retrieve_context: no results from FAISS")
        return []

    chunk_ids = [r[0] for r in results]
    logger.info("retrieve_context: found %d chunks: %s", len(chunk_ids), chunk_ids)

    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.id.in_(chunk_ids))
        .all()
    )
    chunk_map = {c.id: c.content for c in chunks}

    found = [
        {"chunk_id": cid, "content": chunk_map.get(cid, "")}
        for cid, _ in results
        if cid in chunk_map
    ]
    logger.info("retrieve_context: returning %d chunks with content", len(found))
    return found
