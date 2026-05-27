
import httpx

from paperader.collectors.base import BaseCollector, PaperData

DBLP_API_URL = "https://dblp.org/search/publ/api"

# Mapping of common conference abbreviations to DBLP venue keys
CONFERENCE_VENUES = {
    "NeurIPS": "conf/nips",
    "ICML": "conf/icml",
    "ICLR": "conf/iclr",
    "ACL": "conf/acl",
    "EMNLP": "conf/emnlp",
    "NAACL": "conf/naacl",
    "AAAI": "conf/aaai",
    "IJCAI": "conf/ijcai",
    "CVPR": "conf/cvpr",
    "ICCV": "conf/iccv",
    "ECCV": "conf/eccv",
    "KDD": "conf/kdd",
    "WWW": "conf/www",
    "SIGIR": "conf/sigir",
}


class DblpCollector(BaseCollector):
    def __init__(self, max_results: int = 100):
        self.max_results = max_results

    def collect(self, categories: list[str] | None = None, **kwargs) -> list[PaperData]:
        query = kwargs.get("query", "")
        venue = kwargs.get("venue", "")
        year = kwargs.get("year")

        if not query and not venue:
            return []

        return self._search(query=query, venue=venue, year=year)

    def _search(
        self, query: str = "", venue: str = "", year: int | None = None
    ) -> list[PaperData]:
        search_query = query
        if venue:
            # DBLP uses "venue:Name:" syntax in the query string
            venue_name = venue if venue not in CONFERENCE_VENUES else venue
            search_query = f"{search_query} venue:{venue_name}:".strip()

        params = {
            "q": search_query,
            "format": "json",
            "h": min(self.max_results, 1000),
        }

        response = httpx.get(
            DBLP_API_URL, params=params, timeout=30.0, follow_redirects=True
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        papers = []

        for hit in hits:
            info = hit.get("info", {})

            paper_year = int(info.get("year", 0)) if info.get("year") else None
            if year and paper_year and paper_year != year:
                continue

            authors_info = info.get("authors", {}).get("author", [])
            if isinstance(authors_info, dict):
                authors_info = [authors_info]
            authors = [a.get("text", "") if isinstance(a, dict) else str(a) for a in authors_info]

            doi = info.get("doi")
            url = info.get("ee") or info.get("url")

            papers.append(
                PaperData(
                    title=info.get("title", "").rstrip("."),
                    authors=authors,
                    venue=info.get("venue"),
                    year=paper_year,
                    doi=doi,
                    abs_url=url,
                    source="dblp",
                )
            )

        return papers

    def search_conference(
        self, conference: str, year: int | None = None, keywords: list[str] | None = None
    ) -> list[PaperData]:
        # DBLP requires at least one search term; use year or wildcard
        query = " ".join(keywords) if keywords else ""
        if year and not query:
            query = str(year)
        elif not query:
            query = "*"
        return self._search(query=query, venue=conference, year=year)
