import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regla import Regla


async def list_by_negocio(session: AsyncSession, negocio_id: uuid.UUID) -> list[Regla]:
    result = await session.scalars(
        select(Regla)
        .where(Regla.negocio_id == negocio_id)
        .order_by(Regla.posicion, Regla.created_at)
    )
    return list(result)


async def get_by_id(session: AsyncSession, regla_id: uuid.UUID) -> Regla | None:
    return await session.get(Regla, regla_id)


async def next_posicion(session: AsyncSession, negocio_id: uuid.UUID) -> int:
    max_pos = await session.scalar(
        select(func.max(Regla.posicion)).where(Regla.negocio_id == negocio_id)
    )
    return 0 if max_pos is None else max_pos + 1
