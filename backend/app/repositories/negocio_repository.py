import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.negocio import Negocio


async def list_all(session: AsyncSession) -> list[Negocio]:
    result = await session.scalars(
        select(Negocio).order_by(Negocio.created_at.desc(), Negocio.id)
    )
    return list(result)


async def get_by_id(session: AsyncSession, negocio_id: uuid.UUID) -> Negocio | None:
    return await session.get(Negocio, negocio_id)


async def get_by_slug(session: AsyncSession, slug: str) -> Negocio | None:
    return await session.scalar(select(Negocio).where(Negocio.slug == slug))


async def exists_slug(
    session: AsyncSession, slug: str, exclude_id: uuid.UUID | None = None
) -> bool:
    stmt = select(Negocio.id).where(Negocio.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(Negocio.id != exclude_id)
    return await session.scalar(stmt) is not None
