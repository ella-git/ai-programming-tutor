from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.user import MessageResponse, TokenResponse, UserListResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=MessageResponse)
def register(body: UserRegister, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.register(body.username, body.password)
    return MessageResponse(message="注册成功")


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    service = AuthService(db)
    token, user_id = service.login(body.username, body.password)
    return TokenResponse(access_token=token, username=body.username, user_id=user_id)


@router.get("/usersList", response_model=UserListResponse)
def list_users(page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    service = AuthService(db)
    total = service.count_users()
    users = service.list_users(page, page_size)
    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=[
            UserResponse(
                id=u.id,
                username=u.username,
                created_time=u.created_time.isoformat(),
            )
            for u in users
        ],
    )


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.delete_user(user_id)
    return MessageResponse(message="用户已删除")
