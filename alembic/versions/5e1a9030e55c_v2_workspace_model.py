"""v2 workspace model - full schema for AI-native paper management platform

Revision ID: 5e1a9030e55c
Revises:
Create Date: 2026-05-26 17:28:38.455588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e1a9030e55c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Papers table (core, may already exist — use batch for SQLite compat)
    op.create_table(
        'papers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('abstract', sa.Text, nullable=True),
        sa.Column('authors', sa.JSON, nullable=True),
        sa.Column('venue', sa.String(200), nullable=True),
        sa.Column('year', sa.Integer, nullable=True),
        sa.Column('arxiv_id', sa.String(50), nullable=True, unique=True),
        sa.Column('doi', sa.String(200), nullable=True),
        sa.Column('semantic_scholar_id', sa.String(100), nullable=True),
        sa.Column('pdf_path', sa.String(500), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('abs_url', sa.String(500), nullable=True),
        sa.Column('categories', sa.JSON, nullable=True),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('keywords', sa.JSON, nullable=True),
        sa.Column('citation_count', sa.Integer, nullable=True),
        sa.Column('reference_count', sa.Integer, nullable=True),
        sa.Column('tldr', sa.Text, nullable=True),
        sa.Column('influential_citation_count', sa.Integer, nullable=True),
        sa.Column('report', sa.Text, nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='upload'),
        sa.Column('published_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_papers_year_venue', 'papers', ['year', 'venue'])
    op.create_index('ix_papers_source', 'papers', ['source'])
    op.create_index('ix_papers_published', 'papers', ['published_date'])

    # Workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Folders (self-referential tree)
    op.create_table(
        'folders',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('workspace_id', sa.Integer, sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('parent_id', sa.Integer, sa.ForeignKey('folders.id'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_folder_workspace', 'folders', ['workspace_id'])

    # FolderPaper (M:N)
    op.create_table(
        'folder_papers',
        sa.Column('folder_id', sa.Integer, sa.ForeignKey('folders.id'), primary_key=True),
        sa.Column('paper_id', sa.Integer, sa.ForeignKey('papers.id'), primary_key=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Tags (workspace-scoped)
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('workspace_id', sa.Integer, sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(20), nullable=True),
    )
    op.create_index('ix_tag_workspace', 'tags', ['workspace_id'])

    # PaperTag (M:N)
    op.create_table(
        'paper_tags',
        sa.Column('paper_id', sa.Integer, sa.ForeignKey('papers.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer, sa.ForeignKey('tags.id'), primary_key=True),
    )

    # PaperNote
    op.create_table(
        'paper_notes',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('paper_id', sa.Integer, sa.ForeignKey('papers.id'), nullable=False),
        sa.Column('workspace_id', sa.Integer, sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('paper_id', 'workspace_id', name='uq_paper_workspace_note'),
    )
    op.create_index('ix_note_paper', 'paper_notes', ['paper_id'])

    # PaperChunk (RAG)
    op.create_table(
        'paper_chunks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('paper_id', sa.Integer, sa.ForeignKey('papers.id'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('page_num', sa.Integer, nullable=True),
    )
    op.create_index('ix_chunk_paper', 'paper_chunks', ['paper_id'])

    # ChatSession
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('workspace_id', sa.Integer, sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('title', sa.String(200), server_default='New Chat'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_chat_workspace', 'chat_sessions', ['workspace_id'])

    # ChatMessage
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer, sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('referenced_papers', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_msg_session', 'chat_messages', ['session_id'])

    # SyncLog (may already exist)
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('papers_added', sa.Integer, server_default='0'),
        sa.Column('papers_updated', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('paper_chunks')
    op.drop_table('paper_notes')
    op.drop_table('paper_tags')
    op.drop_table('tags')
    op.drop_table('folder_papers')
    op.drop_table('folders')
    op.drop_table('workspaces')
    op.drop_table('sync_logs')
    op.drop_table('papers')
