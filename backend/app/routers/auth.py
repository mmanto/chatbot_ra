from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    Operator,
    clear_auth_cookie,
    create_token,
    set_auth_cookie,
)
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    user = await auth_service.authenticate(db, body.email, body.password)
    token = create_token(user.id, user.email)
    set_auth_cookie(response, token)
    return LoginResponse(user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(response: Response) -> dict:
    clear_auth_cookie(response)
    return {"detail": "Sesión cerrada"}


@router.get("/me", response_model=UserOut)
async def me(operator: Operator) -> UserOut:
    return UserOut.model_validate(operator)
