"""External search service — search arXiv and Semantic Scholar for papers to import."""

import xml.etree.ElementTree as ET

import httpx

from paperader.collectors.semantic_scholar import SemanticScholarClient

ARXIV_API_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def search_arxiv(query: str, max_results: int = 20) -> list[dict]:
    """Search arXiv by keyword query, returns simplified paper dicts."""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        resp = httpx.get(ARXIV_API_URL, params=params, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError:
        return []

    if not resp.text.strip().startswith("<"):
        return []

    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall("atom:entry", NS):
        title = entry.findtext("atom:title", "", NS).replace("\n", " ").strip()
        if not title or "Error" in title:
            continue

        arxiv_id = ""
        id_text = entry.findtext("atom:id", "", NS)
        if id_text:
            arxiv_id = id_text.split("/abs/")[-1]

        authors = [a.findtext("atom:name", "", NS) for a in entry.findall("atom:author", NS)]
        abstract = entry.findtext("atom:summary", "", NS).replace("\n", " ").strip()
        categories = [c.get("term", "") for c in entry.findall("atom:category", NS) if c.get("term")]

        pub_text = entry.findtext("atom:published", "", NS)
        year = None
        if pub_text:
            year = int(pub_text[:4])

        results.append({
            "title": title,
            "authors": authors[:5],
            "abstract": abstract[:300] if abstract else None,
            "arxiv_id": arxiv_id,
            "year": year,
            "categories": categories[:5],
            "source": "arxiv",
        })

    return results


def search_semantic_scholar(query: str, limit: int = 20) -> list[dict]:
    """Search Semantic Scholar, returns simplified paper dicts."""
    client = SemanticScholarClient()
    try:
        raw_results = client.search(query, limit=limit)
    except Exception:
        return []

    results = []
    for item in raw_results:
        if not item.get("title"):
            continue

        authors = [a.get("name", "") for a in (item.get("authors") or [])[:5]]
        ext_ids = item.get("externalIds") or {}

        results.append({
            "title": item["title"],
            "authors": authors,
            "abstract": (item.get("abstract") or "")[:300] or None,
            "arxiv_id": ext_ids.get("ArXiv"),
            "doi": ext_ids.get("DOI"),
            "year": item.get("year"),
            "venue": item.get("venue"),
            "citation_count": item.get("citationCount"),
            "source": "semantic_scholar",
        })

    return results
