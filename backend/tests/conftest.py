"""Fixtures de test: DB `chatbot_ra_test` aislada + cliente HTTP ASGI.

El módulo (importado antes que cualquier módulo de `app`) crea la DB de test si
no existe, apunta DATABASE_URL a ella y aplica las migraciones. Cada test
trunca las tablas y resiembra el operador.
"""
import asyncio
import os
from pathlib import Path

import asyncpg
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text

_ORIGINAL_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/chatbot_ra",
)
TEST_DB_NAME = "chatbot_ra_test"


def _dsn(dbname: str) -> str:
    base = _ORIGINAL_URL.replace("postgresql+asyncpg://", "postgresql://")
    return base.rsplit("/", 1)[0] + "/" + dbname


def _test_url(dbname: str) -> str:
    # Conserva el driver asyncpg para SQLAlchemy
    return _ORIGINAL_URL.rsplit("/", 1)[0] + "/" + dbname


async def _ensure_test_database() -> None:
    conn = await asyncpg.connect(_dsn("postgres"))
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


def _run_migrations() -> None:
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")


# Apuntar la app a la DB de test ANTES de importar cualquier módulo de `app`.
os.environ["DATABASE_URL"] = _test_url(TEST_DB_NAME)
os.environ["TESTING"] = "1"

asyncio.run(_ensure_test_database())
_run_migrations()


@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def authed_client(client):
    """Cliente con sesión de operador iniciada (cookie `ra_token`)."""
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": os.environ["OPERATOR_EMAIL"],
            "password": os.environ["OPERATOR_PASSWORD"],
        },
    )
    assert resp.status_code == 200
    return client


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables_and_seed():
    from app.db.seed import seed_operator
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE users, negocios, reglas, conversaciones, mensajes "
                "RESTART IDENTITY CASCADE"
            )
        )
    await seed_operator()
    yield


async def crear_negocio(client, payload: dict) -> dict:
    resp = await client.post("/api/negocios", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()
