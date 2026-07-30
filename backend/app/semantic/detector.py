import json
import logging
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.semantic_keyword import SemanticKeyword
from app.models.semantic_keyword_embedding import SemanticKeywordEmbedding
from app.utils.embedding_model import get_embedding_model

logger = logging.getLogger(__name__)

THRESHOLD = 0.6


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()


_embed_text = embed_text


def _load_keyword_vectors(db: Session) -> dict[str, list[float]]:
    cached = db.query(SemanticKeywordEmbedding).all()
    kw_map: dict[str, list[float]] = {}
    for c in cached:
        kw_map[c.keyword] = json.loads(c.vector)

    all_keywords = db.query(SemanticKeyword).all()
    need_compute = [k for k in all_keywords if k.keyword not in kw_map]
    if need_compute:
        logger.info("Computing embeddings for %d new keywords", len(need_compute))
        for kw in need_compute:
            vec = embed_text(kw.keyword)
            kw_map[kw.keyword] = vec
            obj = SemanticKeywordEmbedding(keyword=kw.keyword, vector=json.dumps(vec))
            db.add(obj)
        db.commit()

    return kw_map


def detect(db: Session, message_text: str) -> Optional[dict]:
    keyword_vectors = _load_keyword_vectors(db)
    if not keyword_vectors:
        return None

    msg_vec = embed_text(message_text)
    best_keyword = None
    best_score = 0.0

    for keyword, kw_vec in keyword_vectors.items():
        score = _cosine_similarity(msg_vec, kw_vec)
        if score > best_score:
            best_score = score
            best_keyword = keyword

    if best_score >= THRESHOLD:
        logger.info(
            "Trigger detected: keyword=%s score=%.4f message=%.50s",
            best_keyword, best_score, message_text,
        )
        return {"keyword": best_keyword, "score": round(best_score, 4)}

    return None
