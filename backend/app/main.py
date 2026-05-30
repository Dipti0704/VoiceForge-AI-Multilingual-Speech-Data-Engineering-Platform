from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.session import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(
        title="VoiceForge AI",
        description="Multilingual speech data engineering platform.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)
    app.include_router(router, prefix="/api")

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "status": "ok",
            "message": "VoiceForge AI backend is running.",
            "docs": "/docs",
            "api": "/api/health",
        }

    return app


app = create_app()
