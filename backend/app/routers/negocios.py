import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Operator
from app.db.session import get_db
from app.schemas.negocio import NegocioCreate, NegocioOut, NegocioUpdate
from app.services import negocio_service

router = APIRouter(tags=["negocios"])


@router.get("/negocios", response_model=list[NegocioOut])
async def listar_negocios(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> list[NegocioOut]:
    negocios = await negocio_service.listar(db)
    return [NegocioOut.model_validate(n) for n in negocios]


@router.post("/negocios", response_model=NegocioOut)
async def crear_negocio(
    body: NegocioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> NegocioOut:
    negocio = await negocio_service.crear(db, body)
    return NegocioOut.model_validate(negocio)


@router.get("/negocios/{negocio_id}", response_model=NegocioOut)
async def obtener_negocio(
    negocio_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> NegocioOut:
    negocio = await negocio_service.obtener(db, negocio_id)
    return NegocioOut.model_validate(negocio)


@router.patch("/negocios/{negocio_id}", response_model=NegocioOut)
async def actualizar_negocio(
    negocio_id: uuid.UUID,
    body: NegocioUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> NegocioOut:
    negocio = await negocio_service.actualizar(db, negocio_id, body)
    return NegocioOut.model_validate(negocio)


@router.delete("/negocios/{negocio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_negocio(
    negocio_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Operator,
) -> Response:
    await negocio_service.eliminar(db, negocio_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
