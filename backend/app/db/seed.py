"""Seed idempotente: crea el operador único si no existe."""
import asyncio
import logging
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User

logger = logging.getLogger("seed")


async def seed_operator() -> bool:
    """Crea el operador definido por env. Devuelve True si lo creó, False si ya existía."""
    missing = [
        name
        for name, value in (
            ("OPERATOR_EMAIL", settings.operator_email),
            ("OPERATOR_PASSWORD", settings.operator_password),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno requeridas para el seed: "
            + ", ".join(missing)
        )

    async with async_session_factory() as session:
        existing = await session.scalar(
            select(User).where(User.email == settings.operator_email.lower())
        )
        if existing is not None:
            return False

        session.add(
            User(
                email=settings.operator_email.lower(),
                password_hash=hash_password(settings.operator_password),
            )
        )
        await session.commit()
        return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        created = asyncio.run(seed_operator())
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    if created:
        logger.info("operador sembrado: %s", settings.operator_email.lower())
    else:
        logger.info("operador ya existente: %s", settings.operator_email.lower())


if __name__ == "__main__":
    main()
