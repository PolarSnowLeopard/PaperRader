"""
OpenReview API collector for ICLR and NeurIPS accepted papers.

OpenReview hosts paper submissions and decisions for major ML conferences.
API docs: https://docs.openreview.net/
"""

import time

import httpx

from paperader.collectors.base import BaseCollector, PaperData

OPENREVIEW_API = "https://api2.openreview.net"

# Known venue ID patterns for major conferences
VENUE_PATTERNS = {
    "ICLR": "ICLR.cc/{year}/Conference",
    "NeurIPS": "NeurIPS.cc/{year}/Conference",
    "ICML": "ICML.cc/{year}/Conference",
    "COLM": "COLM.cc/{year}/Conference",
    "AAAI": "AAAI.org/{year}/Conference",
}


def resolve_venue_id(conference_key: str) -> str | None:
    """Resolve a conference key like 'ICLR2025' to an OpenReview venue ID."""
    import re

    m = re.match(r"^([A-Za-z]+)(\d{4})$", conference_key)
    if not m:
        return None
    name, year = m.group(1).upper(), m.group(2)
    # Try known patterns first
    for prefix, pattern in VENUE_PATTERNS.items():
        if name == prefix.upper():
            return pattern.format(year=year)
    # Fallback: guess common pattern
    return f"{name}.cc/{year}/Conference"


class OpenReviewCollector(BaseCollector):
    def __init__(self, max_results: int = 200, delay: float = 1.0):
        self.max_results = max_results
        self.delay = delay

    def collect(self, categories: list[str] | None = None, **kwargs) -> list[PaperData]:
        conference = kwargs.get("conference", "ICLR2024")
        return self.get_accepted_papers(conference)

    def get_accepted_papers(self, conference_key: str) -> list[PaperData]:
        venue_id = resolve_venue_id(conference_key)
        if not venue_id:
            return []

        papers = []
        offset = 0
        batch_size = 50

        while offset < self.max_results:
            batch = self._fetch_notes(venue_id, offset, batch_size)
            if not batch:
                break
            papers.extend(batch)
            offset += batch_size
            time.sleep(self.delay)

        return papers

    def _fetch_notes(self, venue_id: str, offset: int, limit: int) -> list[PaperData]:
        params = {
            "content.venueid": venue_id,
            "details": "original",
            "offset": offset,
            "limit": limit,
        }

        try:
            response = httpx.get(
                f"{OPENREVIEW_API}/notes",
                params=params,
                timeout=30.0,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        data = response.json()
        notes = data.get("notes", [])
        papers = []

        for note in notes:
            content = note.get("content", {})

            title = content.get("title", {}).get("value", "")
            if not title:
                continue

            abstract = content.get("abstract", {}).get("value", "")
            authors = content.get("authors", {}).get("value", [])
            keywords = content.get("keywords", {}).get("value", [])

            # Extract venue info from the venue_id
            conf_name = venue_id.split("/")[0].replace(".cc", "")
            year = venue_id.split("/")[1] if "/" in venue_id else ""

            pdf_url = None
            if note.get("id"):
                pdf_url = f"https://openreview.net/pdf?id={note['id']}"

            papers.append(
                PaperData(
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    venue=f"{conf_name} {year}",
                    year=int(year) if year.isdigit() else None,
                    pdf_url=pdf_url,
                    abs_url=f"https://openreview.net/forum?id={note['id']}" if note.get("id") else None,
                    keywords=keywords,
                    source="openreview",
                )
            )

        return papers

    def list_available_conferences(self) -> list[str]:
        import datetime

        year = datetime.datetime.now(datetime.timezone.utc).year
        confs = []
        for name in VENUE_PATTERNS:
            for y in range(year, year - 3, -1):
                confs.append(f"{name}{y}")
        return confs
