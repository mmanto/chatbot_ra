import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NegocioPublicBrief(BaseModel):
    slug: str
    nombre: str


class MensajePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    autor: str
    contenido: str
    created_at: datetime


class StartOut(BaseModel):
    token: uuid.UUID
    negocio: NegocioPublicBrief
    mensajes: list[MensajePublic]


class MessageIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    token: uuid.UUID
    contenido: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    reply: str | None
