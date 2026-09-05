import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Regla(Base):
    __tablename__ = "reglas"
    __table_args__ = (
        UniqueConstraint("negocio_id", "posicion", name="uq_reglas_negocio_posicion"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    negocio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("negocios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    respuesta: Mapped[str] = mapped_column(Text, nullable=False)
    posicion: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
