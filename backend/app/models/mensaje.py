import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Mensaje(Base):
    __tablename__ = "mensajes"
    __table_args__ = (
        CheckConstraint(
            "autor IN ('visitor', 'bot')", name="autor_valido"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversacion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("conversaciones.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    autor: Mapped[str] = mapped_column(String(10), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    # Default en Python (no server_default): `now()` de Postgres es el timestamp
    # de la transacción y mensajes insertados en una misma transacción (visitor +
    # respuesta del bot) quedarían con la misma hora; el UUID v4 no ordena.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
