#!/usr/bin/env python
"""
Daily paper collection script for cron scheduling.

Usage:
    # Run all sources with default categories
    uv run python scripts/daily_collect.py

    # Specify categories and conferences
    uv run python scripts/daily_collect.py --sources arxiv --categories cs.CL,cs.AI

    # Collect from specific conference
    uv run python scripts/daily_collect.py --sources openreview --conference ICLR2025

Cron example (run daily at 8am):
    0 8 * * * cd /path/to/PaperRader && uv run python scripts/daily_collect.py
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paperader.models.base import Base, get_engine, get_session
from paperader.models.sync_log import SyncLog
from paperader.services.paper_service import upsert_papers


def collect_arxiv(session, categories, max_results):
    from paperader.collectors.arxiv import ArxivCollector

    cat_list = categories or ["cs.CL", "cs.AI", "cs.LG"]
    collector = ArxivCollector(max_results=max_results)
    return collector.collect(categories=cat_list)


def collect_openreview(session, conference, max_results):
    from paperader.collectors.openreview import OpenReviewCollector

    collector = OpenReviewCollector(max_results=max_results)
    conf = conference or "ICLR2025"
    return collector.get_accepted_papers(conf)


def collect_acl(session, conference, max_results):
    from paperader.collectors.acl_anthology import AclAnthologyCollector

    collector = AclAnthologyCollector(max_results=max_results)
    conf = conference or "ACL2024"
    return collector.get_conference_papers(conf)


def collect_dblp(session, conference, max_results):
    from paperader.collectors.dblp import DblpCollector

    current_year = datetime.now(timezone.utc).year
    conf = conference or "NeurIPS"
    collector = DblpCollector(max_results=max_results)
    papers = []
    for yr in range(current_year, current_year - 3, -1):
        batch = collector.search_conference(conf, year=yr)
        if batch:
            papers.extend(batch)
            break
    return papers


COLLECTORS = {
    "arxiv": collect_arxiv,
    "openreview": collect_openreview,
    "acl": collect_acl,
    "dblp": collect_dblp,
}


def main():
    parser = argparse.ArgumentParser(description="Daily paper collection")
    parser.add_argument(
        "--sources",
        default="arxiv",
        help="Comma-separated list of sources (arxiv,openreview,acl,dblp)",
    )
    parser.add_argument("--categories", default=None, help="Comma-separated arXiv categories")
    parser.add_argument("--conference", default=None, help="Conference key (e.g. ICLR2025)")
    parser.add_argument("--max-results", type=int, default=200)
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    categories = [c.strip() for c in args.categories.split(",")] if args.categories else None

    engine = get_engine()
    Base.metadata.create_all(engine)

    with get_session() as session:
        for source in sources:
            if source not in COLLECTORS:
                print(f"[SKIP] Unknown source: {source}")
                continue

            log = SyncLog(source=source, status="running")
            session.add(log)
            session.flush()

            try:
                print(f"[{source}] Collecting...")
                if source == "arxiv":
                    papers = collect_arxiv(session, categories, args.max_results)
                else:
                    papers = COLLECTORS[source](session, args.conference, args.max_results)
                added, updated = upsert_papers(session, papers)
                log.status = "success"
                log.papers_added = added
                log.papers_updated = updated
                print(f"[{source}] Done: {added} new, {updated} updated (from {len(papers)} fetched)")
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
                print(f"[{source}] FAILED: {e}")
            finally:
                log.finished_at = datetime.now(timezone.utc)


if __name__ == "__main__":
    main()
