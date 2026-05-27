from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from paperader.config import get_settings
from paperader.models.base import Base, get_engine, get_session
from paperader.models.paper import Paper

app = typer.Typer(name="paperader", help="AI-powered research paper assistant")
console = Console()


@app.command()
def init_db():
    """Initialize the database (create all tables)."""
    engine = get_engine()
    Base.metadata.create_all(engine)

    settings = get_settings()
    Path(settings.pdf_storage_path).mkdir(parents=True, exist_ok=True)

    console.print("[green]Database initialized successfully.[/green]")


@app.command()
def collect(
    source: str = typer.Option("arxiv", help="Data source: arxiv, dblp, openreview, acl"),
    categories: Optional[list[str]] = typer.Option(None, "--cat", help="arXiv categories (e.g. cs.CL)"),
    conference: str = typer.Option(None, help="Conference key (e.g. ICLR2025, ACL2024)"),
    max_results: int = typer.Option(100, help="Maximum papers to collect"),
):
    """Collect papers from specified source."""
    from paperader.models.sync_log import SyncLog
    from paperader.services.paper_service import upsert_papers

    with get_session() as session:
        log = SyncLog(source=source, status="running")
        session.add(log)
        session.flush()

        try:
            if source == "arxiv":
                from paperader.collectors.arxiv import ArxivCollector

                collector = ArxivCollector(max_results=max_results)
                papers = collector.collect(categories=categories or None)
            elif source == "dblp":
                from paperader.collectors.dblp import DblpCollector

                if not conference:
                    console.print("[yellow]Specify --conference (e.g. NeurIPS)[/yellow]")
                    return
                current_year = datetime.now(timezone.utc).year
                collector = DblpCollector(max_results=max_results)
                papers = []
                for yr in range(current_year, current_year - 3, -1):
                    batch = collector.search_conference(conference, year=yr)
                    if batch:
                        papers.extend(batch)
                        break
            elif source == "openreview":
                from paperader.collectors.openreview import OpenReviewCollector

                conf_key = conference or "ICLR2025"
                collector = OpenReviewCollector(max_results=max_results)
                console.print(f"[dim]Fetching {conf_key} from OpenReview...[/dim]")
                papers = collector.get_accepted_papers(conf_key)
                console.print(f"[dim]  Got {len(papers)} papers[/dim]")
            elif source == "acl":
                from paperader.collectors.acl_anthology import AclAnthologyCollector

                conf_key = conference or "ACL2024"
                collector = AclAnthologyCollector(max_results=max_results)
                console.print(f"[dim]Fetching {conf_key} from ACL Anthology...[/dim]")
                papers = collector.get_conference_papers(conf_key)
                console.print(f"[dim]  Got {len(papers)} papers[/dim]")
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
        table.add_column("Venue", style="green", max_width=20)

        for i, paper in enumerate(results, 1):
            table.add_row(str(i), paper.title[:60], str(paper.year or ""), paper.venue or "")

        console.print(table)


@app.command()
def enrich(limit: int = typer.Option(50, help="Max papers to enrich")):
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
                str(i), f"{r.score:.2f}", r.paper.title[:55], str(r.paper.year or ""), r.reason[:40]
            )

        console.print(table)


@app.command()
def stats():
    """Show paper collection statistics."""
    from sqlalchemy import func

    with get_session() as session:
        total = session.query(func.count(Paper.id)).scalar()
        sources = (
            session.query(Paper.source, func.count(Paper.id)).group_by(Paper.source).all()
        )

        console.print("\n[bold]Paper Collection Stats[/bold]")
        console.print(f"  Total papers: [cyan]{total}[/cyan]")
        console.print("\n  [bold]By source:[/bold]")
        for src, count in sources:
            console.print(f"    {src}: [green]{count}[/green]")
        console.print()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
):
    """Start the FastAPI web server."""
    import uvicorn

    console.print(f"[green]Starting server at http://{host}:{port}[/green]")
    uvicorn.run("server.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
