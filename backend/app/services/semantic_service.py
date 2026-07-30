from sqlalchemy.orm import Session

from app.models.semantic_analysis_config import SemanticAnalysisConfig
from app.models.semantic_keyword import SemanticKeyword
from app.models.semantic_keyword_embedding import SemanticKeywordEmbedding


def get_config(db: Session) -> SemanticAnalysisConfig:
    config = db.query(SemanticAnalysisConfig).first()
    if not config:
        config = SemanticAnalysisConfig(interval_minutes=20)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def save_config(db: Session, interval_minutes: int) -> SemanticAnalysisConfig:
    config = db.query(SemanticAnalysisConfig).first()
    if config:
        config.interval_minutes = interval_minutes
    else:
        config = SemanticAnalysisConfig(interval_minutes=interval_minutes)
        db.add(config)
    db.commit()
    db.refresh(config)
    return config


def get_keywords(db: Session) -> list[SemanticKeyword]:
    return db.query(SemanticKeyword).order_by(SemanticKeyword.created_time.desc()).all()


def add_keyword(db: Session, keyword: str) -> SemanticKeyword:
    record = SemanticKeyword(keyword=keyword)
    db.add(record)
    db.commit()
    db.refresh(record)

    from app.utils.embedding_model import get_embedding_model
    import json
    model = get_embedding_model()
    vec = model.encode(keyword, normalize_embeddings=True).tolist()
    existing = db.query(SemanticKeywordEmbedding).filter(
        SemanticKeywordEmbedding.keyword == keyword
    ).first()
    if existing:
        existing.vector = json.dumps(vec)
    else:
        db.add(SemanticKeywordEmbedding(keyword=keyword, vector=json.dumps(vec)))
    db.commit()

    return record


def delete_keyword(db: Session, keyword_id: int) -> bool:
    record = db.query(SemanticKeyword).filter(SemanticKeyword.id == keyword_id).first()
    if not record:
        return False
    db.query(SemanticKeywordEmbedding).filter(
        SemanticKeywordEmbedding.keyword == record.keyword
    ).delete()
    db.delete(record)
    db.commit()
    return True
