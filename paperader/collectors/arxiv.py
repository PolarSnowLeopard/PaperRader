import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from paperader.collectors.base import BaseCollector, PaperData

ARXIV_API_URL = "https://export.arxiv.org/api/query"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivCollector(BaseCollector):
    def __init__(self, max_results: int = 100, delay: float = 3.0):
        self.max_results = max_results
        self.delay = delay

    def collect(self, categories: list[str] | None = None, **kwargs) -> list[PaperData]:
        if not categories:
            categories = ["cs.CL", "cs.AI", "cs.LG"]

        cat_query = " OR ".join(f"cat:{c}" for c in categories)
        query = f"({cat_query})"

        papers = []
        start = 0
        batch_size = min(50, self.max_results)

        while start < self.max_results:
            batch = self._fetch_batch(query, start, batch_size)
            if not batch:
                break
            papers.extend(batch)
            start += batch_size
            if start < self.max_results:
                time.sleep(self.delay)

        return papers

    def _fetch_batch(self, query: str, start: int, max_results: int) -> list[PaperData]:
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        for attempt in range(3):
            try:
                response = httpx.get(
                    ARXIV_API_URL, params=params, timeout=60.0, follow_redirects=True
                )
                response.raise_for_status()
                break
            except httpx.TimeoutException:
                if attempt == 2:
                    raise
                time.sleep(10)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # arXiv rate limiting - wait longer
                    time.sleep(30 * (attempt + 1))
                elif attempt == 2:
                    raise
                else:
                    time.sleep(5)

        root = ET.fromstring(response.text)
        papers = []

        for entry in root.findall("atom:entry", NS):
            entry_id = entry.findtext("atom:id", "", NS)
            arxiv_id = entry_id.split("/abs/")[-1]
            if "v" in arxiv_id:
                arxiv_id = arxiv_id.rsplit("v", 1)[0]

            title = entry.findtext("atom:title", "", NS).replace("\n", " ").strip()
            abstract = entry.findtext("atom:summary", "", NS).replace("\n", " ").strip()

            authors = [
                a.findtext("atom:name", "", NS)
                for a in entry.findall("atom:author", NS)
            ]

            categories = [
                c.get("term", "")
                for c in entry.findall("atom:category", NS)
                if c.get("term")
            ]

            pdf_url = None
            for link in entry.findall("atom:link", NS):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break

            published = None
            pub_text = entry.findtext("atom:published", "", NS)
            if pub_text:
                published = datetime.fromisoformat(pub_text.replace("Z", "+00:00"))

            year = published.year if published else None

            papers.append(
                PaperData(
                    title=title,
                    abstract=abstract or None,
                    authors=authors,
                    year=year,
                    arxiv_id=arxiv_id,
                    pdf_url=pdf_url,
                    abs_url=entry_id,
                    categories=categories,
                    source="arxiv",
                    published_date=published,
                )
            )

        return papers
