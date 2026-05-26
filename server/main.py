from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import papers, search, stats, sync


def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperRader API",
        description="AI-powered research paper assistant",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(papers.router)
    app.include_router(search.router)
    app.include_router(stats.router)
    app.include_router(sync.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
