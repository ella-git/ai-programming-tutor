from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.database.models import SemanticConfig, SemanticKeyword

router = APIRouter()


class ConfigRequest(BaseModel):
    interval_seconds: int


class KeywordRequest(BaseModel):
    keyword: str


class KeywordResponse(BaseModel):
    id: int
    keyword: str
    created_at: str | None = None


class ConfigResponse(BaseModel):
    interval_seconds: int
    keywords: list[KeywordResponse]


@router.get("/api/semantic/config", response_model=ConfigResponse)
def get_semantic_config(db: Session = Depends(get_db)):
    config = db.query(SemanticConfig).first()
    if not config:
        config = SemanticConfig(interval_seconds=20)
        db.add(config)
        db.commit()
        db.refresh(config)

    keywords = db.query(SemanticKeyword).order_by(SemanticKeyword.id).all()
    return ConfigResponse(
        interval_seconds=config.interval_seconds,
        keywords=[
            KeywordResponse(
                id=k.id,
                keyword=k.keyword,
                created_at=k.created_at.isoformat() if k.created_at else None,
            )
            for k in keywords
        ],
    )


@router.post("/api/semantic/config")
def save_semantic_config(request: ConfigRequest, db: Session = Depends(get_db)):
    config = db.query(SemanticConfig).first()
    if not config:
        config = SemanticConfig(interval_seconds=request.interval_seconds)
        db.add(config)
    else:
        config.interval_seconds = request.interval_seconds
    db.commit()
    return {"message": "保存成功"}


@router.post("/api/semantic/keyword", response_model=KeywordResponse)
def add_keyword(request: KeywordRequest, db: Session = Depends(get_db)):
    trimmed = request.keyword.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail="关键词不能为空")

    existing = db.query(SemanticKeyword).filter(SemanticKeyword.keyword == trimmed).first()
    if existing:
        raise HTTPException(status_code=400, detail="关键词已存在")

    record = SemanticKeyword(keyword=trimmed, created_at=datetime.utcnow())
    db.add(record)
    db.commit()
    db.refresh(record)
    return KeywordResponse(
        id=record.id,
        keyword=record.keyword,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )


@router.delete("/api/semantic/keyword/{keyword_id}")
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    record = db.query(SemanticKeyword).filter(SemanticKeyword.id == keyword_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="关键词不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}
