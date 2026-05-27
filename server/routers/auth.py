from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from paperader.models.user import User
from server.auth import create_token, get_current_user, verify_password
from server.deps import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


class UserInfo(BaseModel):
    username: str


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user.username)
    return LoginResponse(token=token, username=user.username)


@router.get("/me", response_model=UserInfo)
def me(username: str = Depends(get_current_user)):
    return UserInfo(username=username)
