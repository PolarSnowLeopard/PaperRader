from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from paperader.config import get_settings
from paperader.models.base import Base, get_engine, get_session
from paperader.models.user import User, UserSubscription
from paperader.models.paper import Paper

app = typer.Typer(name="paperader", help="AI-powered research paper assistant")
console = Console()

DEFAULT_USER = "default"


def _ensure_default_user(session):
    user = session.query(User).filter(User.username == DEFAULT_USER).first()
    if not user:
        user = User(username=DEFAULT_USER)
        session.add(user)
        session.flush()
    return user


@app.command()
def init_db():
    """Initialize the database (create all tables)."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    with get_session() as session:
        _ensure_default_user(session)
    console.print("[green]Database initialized successfully.[/green]")


@app.command()
def collect(
    source: str = typer.Option("arxiv", help="Data source: arxiv, dblp"),
    max_results: int = typer.Option(100, help="Maximum papers to collect"),
):
    """Collect papers from specified source based on subscriptions."""
    from paperader.collectors.arxiv import ArxivCollector
    from paperader.services.paper_service import upsert_papers
    from paperader.models.sync_log import SyncLog

    with get_session() as session:
        user = _ensure_default_user(session)

        # Get user's subscribed categories
        subs = (
            session.query(UserSubscription)
            .filter(UserSubscription.user_id == user.id, UserSubscription.sub_type == "category")
            .all()
        )
        categories = [s.value for s in subs] if subs else None

        log = SyncLog(source=source, status="running")
        session.add(log)
        session.flush()

        try:
            if source == "arxiv":
                collector = ArxivCollector(max_results=max_results)
                papers = collector.collect(categories=categories)
            elif source == "dblp":
                from paperader.collectors.dblp import DblpCollector

                conf_subs = (
                    session.query(UserSubscription)
                    .filter(
                        UserSubscription.user_id == user.id,
                        UserSubscription.sub_type == "conference",
                    )
                    .all()
                )
                current_year = datetime.now(timezone.utc).year
                collector = DblpCollector(max_results=max_results)
                papers = []
                for sub in conf_subs:
                    # Try years from current down to current-2 until we find results
                    for yr in range(current_year, current_year - 3, -1):
                        batch = collector.search_conference(sub.value, year=yr)
                        if batch:
                            papers.extend(batch)
                            break
                if not conf_subs:
                    console.print("[yellow]No conference subscriptions. Use: paperader subscribe --conference NeurIPS[/yellow]")
                    return
            else:
                console.print(f"[red]Unknown source: {source}[/red]")
                return

            added, updated = upsert_papers(session, papers)

            log.status = "success"
            log.papers_added = added
            log.papers_updated = updated
            log.finished_at = datetime.now(timezone.utc)

            console.print(
                f"[green]Collection complete:[/green] {added} new, {updated} updated "
                f"(from {len(papers)} fetched)"
            )
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.finished_at = datetime.now(timezone.utc)
            console.print(f"[red]Collection failed: {e}[/red]")
            raise


@app.command()
def subscribe(
    category: Optional[list[str]] = typer.Option(None, help="arXiv category (e.g. cs.CL)"),
    keyword: Optional[list[str]] = typer.Option(None, help="Keyword to track"),
    conference: Optional[list[str]] = typer.Option(None, help="Conference to monitor"),
    remove: bool = typer.Option(False, "--remove", help="Remove instead of add"),
):
    """Manage topic subscriptions."""
    with get_session() as session:
        user = _ensure_default_user(session)

        items: list[tuple[str, str]] = []
        for c in category or []:
            items.append(("category", c))
        for k in keyword or []:
            items.append(("keyword", k))
        for conf in conference or []:
            items.append(("conference", conf))

        if not items:
            # Show current subscriptions
            subs = session.query(UserSubscription).filter(UserSubscription.user_id == user.id).all()
            if not subs:
                console.print("[yellow]No subscriptions yet. Use --category, --keyword, or --conference to add.[/yellow]")
                return

            table = Table(title="Your Subscriptions")
            table.add_column("Type", style="cyan")
            table.add_column("Value", style="green")
            for s in subs:
                table.add_row(s.sub_type, s.value)
            console.print(table)
            return

        for sub_type, value in items:
            existing = (
                session.query(UserSubscription)
                .filter(
                    UserSubscription.user_id == user.id,
                    UserSubscription.sub_type == sub_type,
                    UserSubscription.value == value,
                )
                .first()
            )

            if remove:
                if existing:
                    session.delete(existing)
                    console.print(f"[red]Removed:[/red] {sub_type} = {value}")
                else:
                    console.print(f"[yellow]Not found:[/yellow] {sub_type} = {value}")
            else:
                if existing:
                    console.print(f"[yellow]Already subscribed:[/yellow] {sub_type} = {value}")
                else:
                    sub = UserSubscription(user_id=user.id, sub_type=sub_type, value=value)
                    session.add(sub)
                    console.print(f"[green]Added:[/green] {sub_type} = {value}")


@app.command()
def search(
    query: str = typer.Argument(help="Search query"),
    limit: int = typer.Option(20, help="Max results"),
):
    """Search papers by keyword in title/abstract."""
    from paperader.services.paper_service import search_papers

    with get_session() as session:
        results = search_papers(session, query, limit=limit)

        if not results:
            console.print("[yellow]No papers found.[/yellow]")
            return

        table = Table(title=f"Search: '{query}' ({len(results)} results)")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="white", max_width=60)
        table.add_column("Year", style="cyan", width=4)
        table.add_column("Categories", style="green", max_width=20)
        table.add_column("arXiv", style="blue", max_width=15)

        for i, paper in enumerate(results, 1):
            cats = ", ".join(paper.categories[:3]) if paper.categories else ""
            table.add_row(
                str(i),
                paper.title[:60],
                str(paper.year or ""),
                cats,
                paper.arxiv_id or "",
            )

        console.print(table)


@app.command()
def enrich(
    limit: int = typer.Option(50, help="Max papers to enrich"),
):
    """Enrich papers with Semantic Scholar data (citations, TLDR)."""
    from paperader.collectors.semantic_scholar import SemanticScholarClient

    with get_session() as session:
        papers = (
            session.query(Paper)
            .filter(Paper.arxiv_id.isnot(None), Paper.citation_count.is_(None))
            .limit(limit)
            .all()
        )

        if not papers:
            console.print("[yellow]No papers to enrich.[/yellow]")
            return

        console.print(f"[dim]Enriching {len(papers)} papers via Semantic Scholar...[/dim]")
        client = SemanticScholarClient()
        enriched = 0

        for paper in papers:
            data = client.enrich_paper(paper.arxiv_id)
            if data:
                for key, value in data.items():
                    if value is not None:
                        setattr(paper, key, value)
                enriched += 1

        console.print(f"[green]Enriched {enriched}/{len(papers)} papers.[/green]")


@app.command(name="smart-search")
def smart_search(
    query: str = typer.Argument(help="Natural language search query"),
    limit: int = typer.Option(10, help="Max results"),
):
    """Semantic search using LLM (intent parsing + re-ranking)."""
    from paperader.search.engine import semantic_search

    with get_session() as session:
        console.print(f"[dim]Searching: '{query}'...[/dim]")
        result = semantic_search(session, query, limit=limit)

        console.print(
            f"\n[bold]Intent:[/bold] {result.intent.intent_summary}"
            f"\n[dim]Candidates scanned: {result.total_candidates} | "
            f"Time: {result.search_time_ms}ms[/dim]\n"
        )

        if not result.results:
            console.print("[yellow]No relevant papers found.[/yellow]")
            return

        table = Table(title=f"Results ({len(result.results)} papers)")
        table.add_column("#", style="dim", width=3)
        table.add_column("Score", style="magenta", width=5)
        table.add_column("Title", style="white", max_width=55)
        table.add_column("Year", style="cyan", width=4)
        table.add_column("Reason", style="dim", max_width=40)

        for i, r in enumerate(result.results, 1):
            table.add_row(
                str(i),
                f"{r.score:.2f}",
                r.paper.title[:55],
                str(r.paper.year or ""),
                r.reason[:40],
            )

        console.print(table)


@app.command()
def stats():
    """Show paper collection statistics."""
    from sqlalchemy import func

    with get_session() as session:
        total = session.query(func.count(Paper.id)).scalar()
        sources = (
            session.query(Paper.source, func.count(Paper.id))
            .group_by(Paper.source)
            .all()
        )
        recent = (
            session.query(func.count(Paper.id))
            .filter(Paper.published_date.isnot(None))
            .scalar()
        )

        console.print(f"\n[bold]Paper Collection Stats[/bold]")
        console.print(f"  Total papers: [cyan]{total}[/cyan]")
        console.print(f"  With publish date: [cyan]{recent}[/cyan]")
        console.print(f"\n  [bold]By source:[/bold]")
        for src, count in sources:
            console.print(f"    {src}: [green]{count}[/green]")
        console.print()


if __name__ == "__main__":
    app()
