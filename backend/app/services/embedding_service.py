import json
import logging

from app.utils.embedding_model import get_embedding_model

logger = logging.getLogger(__name__)


def generate_embedding(text: str) -> list:
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True).tolist()
    return embedding
