import re
import unicodedata
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.negocio import Negocio
from app.repositories import negocio_repository
from app.schemas.negocio import NegocioCreate, NegocioUpdate

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_DASHES_RE = re.compile(r"-+")


def _slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = _NON_ALNUM_RE.sub("-", ascii_text.lower())
    slug = slug.strip("-")
    slug = _DASHES_RE.sub("-", slug)
    return slug


async def _available_slug(
    session: AsyncSession, base: str, exclude_id: uuid.UUID | None = None
) -> str:
    candidate = base or "negocio"
    suffix = 2
    while await negocio_repository.exists_slug(session, candidate, exclude_id=exclude_id):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


async def crear(session: AsyncSession, data: NegocioCreate) -> Negocio:
    if data.slug is not None:
        if await negocio_repository.exists_slug(session, data.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El slug ya está en uso",
            )
        slug = data.slug
    else:
        base = _slugify(data.nombre)
        slug = await _available_slug(session, base)

    negocio = Negocio(slug=slug, nombre=data.nombre)
    session.add(negocio)
    await session.commit()
    await session.refresh(negocio)
    return negocio


async def listar(session: AsyncSession) -> list[Negocio]:
    return await negocio_repository.list_all(session)


async def obtener(session: AsyncSession, negocio_id: uuid.UUID) -> Negocio:
    negocio = await negocio_repository.get_by_id(session, negocio_id)
    if negocio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado",
        )
    return negocio


async def actualizar(
    session: AsyncSession, negocio_id: uuid.UUID, data: NegocioUpdate
) -> Negocio:
    negocio = await obtener(session, negocio_id)
    cambios = data.model_dump(exclude_unset=True)

    if "slug" in cambios:
        slug = cambios["slug"]
        if slug != negocio.slug and await negocio_repository.exists_slug(
            session, slug, exclude_id=negocio.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El slug ya está en uso",
            )
        negocio.slug = slug

    if "nombre" in cambios:
        negocio.nombre = cambios["nombre"]

    # greeting/default_reply: trim + vacío → null
    for campo in ("greeting", "default_reply"):
        if campo in cambios:
            valor = cambios[campo]
            negocio.__setattr__(campo, valor.strip() if valor else None)

    for campo in ("activo", "autoresponder"):
        if campo in cambios:
            negocio.__setattr__(campo, cambios[campo])

    await session.commit()
    await session.refresh(negocio)
    return negocio


async def eliminar(session: AsyncSession, negocio_id: uuid.UUID) -> None:
    negocio = await obtener(session, negocio_id)
    await session.delete(negocio)
    await session.commit()
