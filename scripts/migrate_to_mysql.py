#!/usr/bin/env python
"""
Migrate data from SQLite to MySQL.

Usage:
    1. Set PAPERADER_MYSQL_URL to your MySQL connection string:
       export PAPERADER_MYSQL_URL="mysql+pymysql://user:pass@host:3306/paperader?charset=utf8mb4"

    2. Run:
       uv run python scripts/migrate_to_mysql.py

This script:
- Reads all data from the current SQLite database
- Creates tables in MySQL
- Inserts all records preserving IDs and relationships
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from paperader.config import get_settings
from paperader.models.base import Base, get_engine
from paperader.models.paper import Paper
from paperader.models.sync_log import SyncLog
from paperader.models.workspace import Workspace, Folder, FolderPaper
from paperader.models.tag import Tag, PaperTag
from paperader.models.note import PaperNote
from paperader.models.chunk import PaperChunk
from paperader.models.chat import ChatSession, ChatMessage

MODELS = [
    Paper, SyncLog,
    Workspace, Folder, FolderPaper,
    Tag, PaperTag,
    PaperNote, PaperChunk,
    ChatSession, ChatMessage,
]


def migrate(mysql_url: str):
    sqlite_engine = get_engine()
    sqlite_session = sessionmaker(bind=sqlite_engine)()

    mysql_engine = create_engine(mysql_url, echo=False)
    Base.metadata.create_all(mysql_engine)
    mysql_session = sessionmaker(bind=mysql_engine)()

    for model in MODELS:
        table_name = model.__tablename__
        records = sqlite_session.query(model).all()
        print(f"[{table_name}] Migrating {len(records)} records...")

        for record in records:
            data = {}
            for col in model.__table__.columns:
                data[col.name] = getattr(record, col.name)
            mysql_session.execute(model.__table__.insert().values(**data))

        mysql_session.commit()
        print(f"[{table_name}] Done.")

    sqlite_session.close()
    mysql_session.close()
    print("\nMigration complete!")


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to MySQL")
    parser.add_argument(
        "--mysql-url",
        default=os.environ.get("PAPERADER_MYSQL_URL"),
        help="MySQL connection string (or set PAPERADER_MYSQL_URL env var)",
    )
    args = parser.parse_args()

    if not args.mysql_url:
        print("ERROR: Provide --mysql-url or set PAPERADER_MYSQL_URL")
        print("Example: mysql+pymysql://user:pass@host:3306/paperader?charset=utf8mb4")
        sys.exit(1)

    print(f"Source: {get_settings().database_url}")
    print(f"Target: {args.mysql_url}")
    print()

    migrate(args.mysql_url)


if __name__ == "__main__":
    main()
