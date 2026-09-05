import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.public import (
    MensajePublic,
    MessageIn,
    MessageOut,
    StartOut,
)
from app.services import chat_service

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/{slug}/start", response_model=StartOut)
async def start_chat(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StartOut:
    resultado = await chat_service.iniciar(db, slug)
    return StartOut(
        token=resultado["token"],
        negocio=resultado["negocio"],
        mensajes=[MensajePublic.model_validate(m) for m in resultado["mensajes"]],
    )


@router.post("/{slug}/message", response_model=MessageOut)
async def send_message(
    slug: str,
    body: MessageIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageOut:
    reply = await chat_service.enviar(db, slug, body.token, body.contenido)
    return MessageOut(reply=reply)


@router.get("/{slug}/history", response_model=list[MensajePublic])
async def chat_history(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: uuid.UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MensajePublic]:
    mensajes = await chat_service.historial(db, slug, token, limit)
    return [MensajePublic.model_validate(m) for m in mensajes]
