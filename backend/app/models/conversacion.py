import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Conversacion(Base):
    __tablename__ = "conversaciones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    negocio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("negocios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, index=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
