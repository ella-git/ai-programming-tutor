import logging

logger = logging.getLogger(__name__)

_model = None
_model_name = "BAAI/bge-small-zh-v1.5"


def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", _model_name)
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_model_name)
        logger.info("Embedding model loaded successfully")
    return _model
