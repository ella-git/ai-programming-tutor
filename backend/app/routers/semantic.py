from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.services.semantic_service import (
    add_keyword,
    delete_keyword,
    get_config,
    get_keywords,
    save_config,
)

router = APIRouter(prefix="/api/semantic", tags=["语义分析配置"])


class KeywordItem(BaseModel):
    id: int
    keyword: str
    created_at: str | None = None


class ConfigResponse(BaseModel):
    interval_seconds: int
    keywords: list[KeywordItem]


class SaveConfigRequest(BaseModel):
    interval_seconds: int


class AddKeywordRequest(BaseModel):
    keyword: str


class AddKeywordResponse(BaseModel):
    id: int
    keyword: str
    created_at: str | None = None


@router.get("/config", response_model=ConfigResponse)
def get_semantic_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = get_config(db)
    keyword_records = get_keywords(db)
    return ConfigResponse(
        interval_seconds=config.interval_minutes,
        keywords=[
            KeywordItem(
                id=k.id,
                keyword=k.keyword,
                created_at=k.created_time.isoformat() if k.created_time else None,
            )
            for k in keyword_records
        ],
    )


@router.post("/config")
def save_semantic_config(
    body: SaveConfigRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.interval_seconds < 1:
        raise HTTPException(status_code=400, detail="间隔时间必须大于0")
    save_config(db, body.interval_seconds)
    return {"success": True}


@router.post("/keyword", response_model=AddKeywordResponse)
def add_semantic_keyword(
    body: AddKeywordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not body.keyword or not body.keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    record = add_keyword(db, body.keyword.strip())
    return AddKeywordResponse(
        id=record.id,
        keyword=record.keyword,
        created_at=record.created_time.isoformat() if record.created_time else None,
    )


@router.delete("/keyword/{keyword_id}")
def delete_semantic_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = delete_keyword(db, keyword_id)
    if not ok:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return {"success": True}
