"""
OpenReview API collector for ICLR and NeurIPS accepted papers.

OpenReview hosts paper submissions and decisions for major ML conferences.
API docs: https://docs.openreview.net/
"""

import time

import httpx

from paperader.collectors.base import BaseCollector, PaperData

OPENREVIEW_API = "https://api2.openreview.net"

# Venue IDs for major conferences (updated yearly)
VENUE_IDS = {
    "ICLR2025": "ICLR.cc/2025/Conference",
    "ICLR2024": "ICLR.cc/2024/Conference",
    "NeurIPS2024": "NeurIPS.cc/2024/Conference",
    "NeurIPS2023": "NeurIPS.cc/2023/Conference",
    "ICML2024": "ICML.cc/2024/Conference",
    "ICML2025": "ICML.cc/2025/Conference",
}


class OpenReviewCollector(BaseCollector):
    def __init__(self, max_results: int = 200, delay: float = 1.0):
        self.max_results = max_results
        self.delay = delay

    def collect(self, categories: list[str] | None = None, **kwargs) -> list[PaperData]:
        conference = kwargs.get("conference", "ICLR2024")
        return self.get_accepted_papers(conference)

    def get_accepted_papers(self, conference_key: str) -> list[PaperData]:
        venue_id = VENUE_IDS.get(conference_key)
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
        return list(VENUE_IDS.keys())
