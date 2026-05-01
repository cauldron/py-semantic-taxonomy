from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from py_semantic_taxonomy.adapters.persistence.database import (
    create_engine,
    init_db,
)
from py_semantic_taxonomy.adapters.routers.admin_router import router as admin_router
from py_semantic_taxonomy.adapters.routers.api_router import api_router
from py_semantic_taxonomy.adapters.routers.catch_router import router as catch_router
from py_semantic_taxonomy.adapters.routers.contributor_router import router as contributor_router
from py_semantic_taxonomy.adapters.routers.web_router import router as web_router
from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.dependencies import get_search_service

# from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI()
    settings = get_settings()
    app.add_middleware(SessionMiddleware, secret_key=settings.admin_session_secret)

    @app.on_event("startup")
    async def database():
        await init_db(create_engine())

    @app.on_event("startup")
    async def search():
        ts = get_search_service()
        if ts.configured:
            await ts.initialize()

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=settings.allow_origins,
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    app.include_router(api_router)
    app.include_router(web_router)
    app.include_router(admin_router)
    app.include_router(contributor_router)
    app.include_router(catch_router)
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "adapters" / "routers" / "static"),
        name="static",
    )
    return app


def test_app() -> FastAPI:
    app = FastAPI()
    settings = get_settings()
    app.add_middleware(SessionMiddleware, secret_key=settings.admin_session_secret)
    app.include_router(api_router)
    app.include_router(web_router)
    app.include_router(admin_router)
    app.include_router(contributor_router)
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "py_semantic_taxonomy.app:create_app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )
