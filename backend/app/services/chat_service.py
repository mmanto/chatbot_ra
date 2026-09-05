import asyncio
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.negocio import Negocio
from app.repositories import (
    conversacion_repository,
    mensaje_repository,
    negocio_repository,
    regla_repository,
)
from app.services import bot_engine

REPLY_DELAY_SECONDS = 0.7


def _no_disponible() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="no_disponible",
    )


async def _negocio_activo(session: AsyncSession, slug: str) -> Negocio:
    negocio = await negocio_repository.get_by_slug(session, slug)
    if negocio is None or not negocio.activo:
        raise _no_disponible()
    return negocio


async def _conversacion_valida(
    session: AsyncSession, negocio: Negocio, token: uuid.UUID
):
    conversacion = await conversacion_repository.get_by_token_and_negocio(
        session, token, negocio.id
    )
    if conversacion is None:
        raise _no_disponible()
    return conversacion


async def iniciar(session: AsyncSession, slug: str) -> dict:
    negocio = await _negocio_activo(session, slug)
    conversacion = await conversacion_repository.create(session, negocio.id)

    mensajes = []
    if negocio.autoresponder and negocio.greeting:
        mensajes.append(
            await mensaje_repository.add(session, conversacion.id, "bot", negocio.greeting)
        )

    await session.commit()
    return {
        "token": conversacion.token,
        "negocio": {"slug": negocio.slug, "nombre": negocio.nombre},
        "mensajes": mensajes,
    }


async def enviar(session: AsyncSession, slug: str, token: uuid.UUID, contenido: str) -> str | None:
    negocio = await _negocio_activo(session, slug)
    conversacion = await _conversacion_valida(session, negocio, token)

    await mensaje_repository.add(session, conversacion.id, "visitor", contenido)

    reply = None
    if negocio.autoresponder:
        reglas = await regla_repository.list_by_negocio(session, negocio.id)
        reply = bot_engine.bot_reply(contenido, reglas, negocio.default_reply)
        if reply:
            # Efecto "escribiendo…" (configuración fija en el MVP)
            await asyncio.sleep(REPLY_DELAY_SECONDS)
            await mensaje_repository.add(session, conversacion.id, "bot", reply)

    await session.commit()
    return reply


async def historial(
    session: AsyncSession, slug: str, token: uuid.UUID, limit: int
) -> list:
    negocio = await _negocio_activo(session, slug)
    conversacion = await _conversacion_valida(session, negocio, token)
    return await mensaje_repository.list_recent(session, conversacion.id, limit)
