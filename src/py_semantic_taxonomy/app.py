from fastapi import FastAPI

from py_semantic_taxonomy.adapters.routers.router import router

# from fastapi.middleware.cors import CORSMiddleware
# from fastapi_pagination import add_pagination


def create_app():
    app = FastAPI()
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=settings.allow_origins,
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    app.include_router(router)
    # add_pagination(app)
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
