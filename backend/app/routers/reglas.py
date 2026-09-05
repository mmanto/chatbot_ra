import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Operator
from app.db.session import get_db
from app.schemas.regla import ReglaCreate, ReglaOrder, ReglaOut, ReglaUpdate
from app.services import regla_service

router = APIRouter(tags=["reglas"])


@router.get("/negocios/{negocio_id}/reglas", response_model=list[ReglaOut])
async def listar_reglas(
    negocio_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> list[ReglaOut]:
    reglas = await regla_service.listar(db, negocio_id)
    return [ReglaOut.model_validate(r) for r in reglas]


@router.post("/negocios/{negocio_id}/reglas", response_model=ReglaOut)
async def crear_regla(
    negocio_id: uuid.UUID,
    body: ReglaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> ReglaOut:
    regla = await regla_service.crear(db, negocio_id, body)
    return ReglaOut.model_validate(regla)


@router.put("/negocios/{negocio_id}/reglas/orden", response_model=list[ReglaOut])
async def reordenar_reglas(
    negocio_id: uuid.UUID,
    body: ReglaOrder,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> list[ReglaOut]:
    reglas = await regla_service.reordenar(db, negocio_id, body)
    return [ReglaOut.model_validate(r) for r in reglas]


@router.patch("/reglas/{regla_id}", response_model=ReglaOut)
async def actualizar_regla(
    regla_id: uuid.UUID,
    body: ReglaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> ReglaOut:
    regla = await regla_service.actualizar(db, regla_id, body)
    return ReglaOut.model_validate(regla)


@router.delete("/reglas/{regla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_regla(
    regla_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> Response:
    await regla_service.eliminar(db, regla_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
