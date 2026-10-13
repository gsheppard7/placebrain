import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import database
from app.config import Settings, resolve_database_url
from app.errors import DomainError
from app.migrate import upgrade_database
from app.routers import objects, scans, spaces
from app.seed import seed

logger = logging.getLogger("placebrain")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = Settings()
    url = resolve_database_url(settings.database_url)
    upgrade_database(url)
    database.init_db(url)
    if settings.seed_on_startup and database.SessionLocal is not None:
        db = database.SessionLocal()
        try:
            if seed(db):
                logger.info("Seeded the fictional Riverside equipment room")
        finally:
            db.close()
    yield
    if database.engine is not None:
        database.engine.dispose()


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="PlaceBrain", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(spaces.router)
    app.include_router(objects.router)
    app.include_router(scans.router)
    return app


app = create_app()
