from fastapi import FastAPI

from py_semantic_taxonomy.adapters.persistence.database import (
    create_engine,
    init_db,
)
from py_semantic_taxonomy.adapters.routers.router import router
from py_semantic_taxonomy.dependencies import get_search_service

# from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI()

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

    app.include_router(router)
    return app


def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
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
