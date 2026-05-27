from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import auth, chat, folders, notes, papers, report, search, sync, tags, workspaces


def create_app() -> FastAPI:
    app = FastAPI(
        title="PaperRader API",
        description="AI-powered research paper management platform",
        version="2.0.0",
    )

    @app.on_event("startup")
    def _init_db():
        from sqlalchemy import inspect, text
        from paperader.models import Base
        from paperader.models.base import get_engine
        from paperader.config import get_settings

        engine = get_engine()
        Base.metadata.create_all(engine)
        Path(get_settings().pdf_storage_path).mkdir(parents=True, exist_ok=True)

        with engine.connect() as conn:
            inspector = inspect(engine)
            if "papers" in inspector.get_table_names():
                cols = {c["name"] for c in inspector.get_columns("papers")}
                if "report" not in cols:
                    conn.execute(text("ALTER TABLE papers ADD COLUMN report TEXT"))
                    conn.commit()

        from paperader.models.user import User
        from server.auth import hash_password

        SessionLocal = __import__("sqlalchemy.orm", fromlist=["sessionmaker"]).sessionmaker(bind=engine)
        db = SessionLocal()
        try:
            if db.query(User).count() == 0:
                db.add(User(username="admin", password_hash=hash_password("123456")))
                db.commit()
        finally:
            db.close()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://eblab.club:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(workspaces.router)
    app.include_router(folders.router)
    app.include_router(tags.router)
    app.include_router(notes.router)
    app.include_router(papers.router)
    app.include_router(report.router)
    app.include_router(chat.router)
    app.include_router(search.router)
    app.include_router(sync.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
