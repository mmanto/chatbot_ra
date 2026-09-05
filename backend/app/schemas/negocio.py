import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class NegocioCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, pattern=SLUG_PATTERN, max_length=120)


class NegocioUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, pattern=SLUG_PATTERN, max_length=120)
    greeting: str | None = None
    default_reply: str | None = None
    activo: bool | None = None
    autoresponder: bool | None = None


class NegocioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: uuid.UUID
    slug: str
    nombre: str
    greeting: str | None
    default_reply: str | None
    activo: bool
    autoresponder: bool
    created_at: datetime
    updated_at: datetime
