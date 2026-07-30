import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel

from app.core.config import UPLOAD_DIR
from app.core.exceptions import AppException
from app.core.security import get_current_user
from app.database.models import User

router = APIRouter(prefix="/api/upload", tags=["上传"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class UploadResponse(BaseModel):
    url: str


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(f"不支持的文件格式: {ext}", status_code=400)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise AppException("文件大小不能超过 10MB", status_code=400)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    return UploadResponse(url=f"/uploads/{filename}")
