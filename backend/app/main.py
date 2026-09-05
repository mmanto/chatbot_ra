from fastapi import FastAPI

from app.routers import auth, negocios, public, reglas


def create_app() -> FastAPI:
    app = FastAPI(
        title="chatbot_ra API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api")
    app.include_router(negocios.router, prefix="/api")
    app.include_router(reglas.router, prefix="/api")
    app.include_router(public.router, prefix="/api")

    return app


app = create_app()
