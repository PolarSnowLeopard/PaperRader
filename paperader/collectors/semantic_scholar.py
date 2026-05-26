import time

import httpx

from paperader.config import get_settings

S2_API_URL = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,abstract,authors,year,venue,citationCount,referenceCount,tldr,influentialCitationCount,externalIds"


class SemanticScholarClient:
    def __init__(self):
        settings = get_settings()
        self.headers = {}
        if settings.s2_api_key:
            self.headers["x-api-key"] = settings.s2_api_key
        self.delay = 1.0 if settings.s2_api_key else 3.0

    def search(self, query: str, limit: int = 20, year: str | None = None) -> list[dict]:
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": S2_FIELDS,
        }
        if year:
            params["year"] = year

        response = httpx.get(
            f"{S2_API_URL}/paper/search",
            params=params,
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    def get_paper_by_arxiv_id(self, arxiv_id: str) -> dict | None:
        response = httpx.get(
            f"{S2_API_URL}/paper/arXiv:{arxiv_id}",
            params={"fields": S2_FIELDS},
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def enrich_paper(self, arxiv_id: str) -> dict | None:
        data = self.get_paper_by_arxiv_id(arxiv_id)
        if not data:
            return None

        return {
            "semantic_scholar_id": data.get("paperId"),
            "citation_count": data.get("citationCount"),
            "reference_count": data.get("referenceCount"),
            "influential_citation_count": data.get("influentialCitationCount"),
            "tldr": data.get("tldr", {}).get("text") if data.get("tldr") else None,
            "venue": data.get("venue") or None,
        }

    def batch_enrich(self, arxiv_ids: list[str]) -> dict[str, dict]:
        results = {}
        for arxiv_id in arxiv_ids:
            try:
                data = self.enrich_paper(arxiv_id)
                if data:
                    results[arxiv_id] = data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    time.sleep(60)
                    try:
                        data = self.enrich_paper(arxiv_id)
                        if data:
                            results[arxiv_id] = data
                    except Exception:
                        pass
            time.sleep(self.delay)
        return results
