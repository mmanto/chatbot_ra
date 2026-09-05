from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# En tests (settings.testing) se usa NullPool: cada request abre su propia
# conexión dentro del event loop del test (pytest-asyncio crea un loop por test).
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool if settings.testing else None,
    echo=False,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
