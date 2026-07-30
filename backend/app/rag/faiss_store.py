import json
import logging
import os
import threading

import faiss
import numpy as np

from app.core.config import FAISS_INDEX_DIR

logger = logging.getLogger(__name__)

_index = None
_id_to_chunk = {}
_lock = threading.Lock()


def build_index():
    from app.database.database import SessionLocal
    from app.models.knowledge_embedding import KnowledgeEmbedding

    db = SessionLocal()
    try:
        records = db.query(KnowledgeEmbedding).all()
        if not records:
            logger.warning("build_index: no embeddings found in DB")
            return False

        vectors = []
        mapping = {}
        for i, rec in enumerate(records):
            vectors.append(json.loads(rec.embedding))
            mapping[i] = rec.chunk_id

        matrix = np.array(vectors).astype(np.float32)
        dim = matrix.shape[1]

        index = faiss.IndexFlatIP(dim)
        index.add(matrix)

        os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
        faiss.write_index(index, os.path.join(FAISS_INDEX_DIR, "knowledge.index"))
        with open(os.path.join(FAISS_INDEX_DIR, "id_map.json"), "w") as f:
            json.dump(mapping, f)

        global _index, _id_to_chunk
        with _lock:
            _index = index
            _id_to_chunk = {int(k): int(v) for k, v in mapping.items()}

        logger.info("build_index: %d vectors added, dim=%d", len(records), dim)
        return True
    finally:
        db.close()


def load_index():
    global _index, _id_to_chunk
    if _index is not None:
        return True

    with _lock:
        if _index is not None:
            return True

        index_path = os.path.join(FAISS_INDEX_DIR, "knowledge.index")
        map_path = os.path.join(FAISS_INDEX_DIR, "id_map.json")

        if not os.path.exists(index_path) or not os.path.exists(map_path):
            logger.warning("load_index: index files not found at %s", index_path)
            return False

        _index = faiss.read_index(index_path)
        with open(map_path, "r") as f:
            raw = json.load(f)
        _id_to_chunk = {int(k): int(v) for k, v in raw.items()}
        logger.info("load_index: loaded %d vectors", _index.ntotal)
        return True


def search(query_vector: list, top_k: int = 5):
    if not load_index():
        return []

    matrix = np.array([query_vector]).astype(np.float32)
    scores, indices = _index.search(matrix, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue
        chunk_id = _id_to_chunk[int(idx)]
        results.append((chunk_id, float(scores[0][i])))

    logger.debug("search: top_k=%d, results=%d, top_score=%.4f", top_k, len(results), results[0][1] if results else 0)
    return results


def index_exists() -> bool:
    index_path = os.path.join(FAISS_INDEX_DIR, "knowledge.index")
    return os.path.exists(index_path)


def index_size() -> int:
    global _index
    if _index is not None:
        return _index.ntotal
    return 0
