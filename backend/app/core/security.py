"""Seguridad del panel de operador: hash de contraseñas + cookie-JWT.

Decisión (sin token CSRF): la cookie `ra_token` se emite con SameSite=Lax y la
API solo es alcanzable same-origin a través de los rewrites de Next.js (el
navegador nunca habla directo con la API). Si en el futuro la API se sirve en
otro origen, hay que añadir CORS restringido y un mecanismo CSRF.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, Response, status
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

COOKIE_NAME = "ra_token"
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_hash.verify(plain, hashed)
    except Exception:
        return False


def create_token(user_id: uuid.UUID, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expires_min),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=settings.app_public_url.startswith("https"),
        max_age=settings.jwt_expires_min * 60,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/", samesite="lax")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
    )


async def get_operator(
    db: Annotated[AsyncSession, Depends(get_db)],
    ra_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """Dependencia que autentica al operador vía cookie `ra_token`."""
    if not ra_token:
        raise _credentials_exception()

    payload = decode_token(ra_token)
    if not payload or not payload.get("sub"):
        raise _credentials_exception()

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise _credentials_exception()

    user = await db.get(User, user_id)
    if user is None:
        raise _credentials_exception()
    return user


Operator = Annotated[User, Depends(get_operator)]
