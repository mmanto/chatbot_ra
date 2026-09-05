import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversacion import Conversacion


async def create(session: AsyncSession, negocio_id: uuid.UUID) -> Conversacion:
    conversacion = Conversacion(negocio_id=negocio_id)
    session.add(conversacion)
    await session.flush()
    return conversacion


async def get_by_token_and_negocio(
    session: AsyncSession, token: uuid.UUID, negocio_id: uuid.UUID
) -> Conversacion | None:
    return await session.scalar(
        select(Conversacion).where(
            Conversacion.token == token,
            Conversacion.negocio_id == negocio_id,
        )
    )
