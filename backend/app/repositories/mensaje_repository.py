import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje import Mensaje


async def add(
    session: AsyncSession,
    conversacion_id: uuid.UUID,
    autor: str,
    contenido: str,
) -> Mensaje:
    mensaje = Mensaje(conversacion_id=conversacion_id, autor=autor, contenido=contenido)
    session.add(mensaje)
    await session.flush()
    await session.refresh(mensaje)
    return mensaje


async def list_recent(
    session: AsyncSession, conversacion_id: uuid.UUID, limit: int
) -> list[Mensaje]:
    """Últimos `limit` mensajes en orden ascendente."""
    result = await session.scalars(
        select(Mensaje)
        .where(Mensaje.conversacion_id == conversacion_id)
        .order_by(Mensaje.created_at.desc(), Mensaje.id.desc())
        .limit(limit)
    )
    return list(reversed(list(result)))
