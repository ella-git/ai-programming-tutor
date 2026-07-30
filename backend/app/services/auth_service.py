from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.database.models import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, username: str, password: str) -> User:
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            raise AppException("用户名已存在", status_code=409)
        user = User(username=username, password_hash=hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, username: str, password: str) -> tuple[str, int]:
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            raise AppException("用户名或密码错误", status_code=401)
        token = create_access_token({"sub": str(user.id), "username": user.username})
        return token, user.id

    def list_users(self, page: int = 1, page_size: int = 50) -> list[User]:
        skip = (page - 1) * page_size
        return self.db.query(User).offset(skip).limit(page_size).all()

    def count_users(self) -> int:
        return self.db.query(User).count()

    def delete_user(self, user_id: int) -> None:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AppException("用户不存在", status_code=404)
        self.db.delete(user)
        self.db.commit()
