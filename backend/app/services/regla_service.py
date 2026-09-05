import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regla import Regla
from app.repositories import negocio_repository, regla_repository
from app.schemas.regla import ReglaCreate, ReglaOrder, ReglaUpdate
from app.services import negocio_service


def _regla_404() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Regla no encontrada",
    )


async def listar(session: AsyncSession, negocio_id: uuid.UUID) -> list[Regla]:
    await negocio_service.obtener(session, negocio_id)  # 404 si el negocio no existe
    return await regla_repository.list_by_negocio(session, negocio_id)


async def crear(
    session: AsyncSession, negocio_id: uuid.UUID, data: ReglaCreate
) -> Regla:
    negocio = await negocio_service.obtener(session, negocio_id)  # 404
    posicion = await regla_repository.next_posicion(session, negocio.id)
    regla = Regla(
        negocio_id=negocio.id,
        keyword=data.keyword,
        respuesta=data.respuesta,
        posicion=posicion,
    )
    session.add(regla)
    await session.commit()
    await session.refresh(regla)
    return regla


async def actualizar(session: AsyncSession, regla_id: uuid.UUID, data: ReglaUpdate) -> Regla:
    regla = await regla_repository.get_by_id(session, regla_id)
    if regla is None:
        raise _regla_404()

    cambios = data.model_dump(exclude_unset=True)
    for campo in ("keyword", "respuesta"):
        if campo in cambios:
            regla.__setattr__(campo, cambios[campo])

    await session.commit()
    await session.refresh(regla)
    return regla


async def eliminar(session: AsyncSession, regla_id: uuid.UUID) -> None:
    regla = await regla_repository.get_by_id(session, regla_id)
    if regla is None:
        raise _regla_404()
    await session.delete(regla)
    await session.commit()


async def reordenar(
    session: AsyncSession, negocio_id: uuid.UUID, body: ReglaOrder
) -> list[Regla]:
    negocio = await negocio_service.obtener(session, negocio_id)  # 404
    reglas = await regla_repository.list_by_negocio(session, negocio.id)
    reglas_por_id = {r.id: r for r in reglas}

    # Duplicados en el body → 422
    if len(body.regla_ids) != len(set(body.regla_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El listado contiene reglas duplicadas",
        )

    # Una regla ajena al negocio → 404 (pertenencia)
    desconocidas = [rid for rid in body.regla_ids if rid not in reglas_por_id]
    if desconocidas:
        raise _regla_404()

    # Faltan reglas del negocio en el listado → 422
    if len(body.regla_ids) != len(reglas):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El listado debe incluir todas las reglas del negocio",
        )

    # Dos fases dentro de la misma transacción: primero liberar los valores
    # 0..n-1 con posiciones negativas únicas, luego asignar el orden final
    # (evita choques transitorios con la constraint (negocio_id, posicion)).
    for idx, regla_id in enumerate(body.regla_ids):
        reglas_por_id[regla_id].posicion = -(idx + 1)
    await session.flush()

    for posicion, regla_id in enumerate(body.regla_ids):
        reglas_por_id[regla_id].posicion = posicion

    await session.commit()
    return await regla_repository.list_by_negocio(session, negocio.id)
