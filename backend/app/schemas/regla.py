import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReglaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    keyword: str = Field(min_length=1, max_length=200)
    respuesta: str = Field(min_length=1)


class ReglaUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    keyword: str | None = Field(default=None, min_length=1, max_length=200)
    respuesta: str | None = Field(default=None, min_length=1)


class ReglaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    negocio_id: uuid.UUID
    keyword: str
    respuesta: str
    posicion: int
    created_at: datetime


class ReglaOrder(BaseModel):
    regla_ids: list[uuid.UUID] = Field(min_length=1)
