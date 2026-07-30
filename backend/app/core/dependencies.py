from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.database.database import get_db
from app.database.models import User

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppException("请先登录", status_code=401)
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise AppException("无效或过期的令牌", status_code=401)
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise AppException("用户不存在", status_code=401)
    return user
