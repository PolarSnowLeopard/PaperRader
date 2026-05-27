"""Paper import service — handles PDF download and metadata fetching."""

import hashlib
import re
from pathlib import Path

import httpx

from paperader.collectors.base import PaperData
from paperader.config import get_settings


def get_pdf_storage_dir() -> Path:
    path = Path(get_settings().pdf_storage_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_pdf_file(content: bytes, filename: str | None = None) -> str:
    storage = get_pdf_storage_dir()
    if not filename:
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        filename = f"{file_hash}.pdf"
    filepath = storage / filename
    filepath.write_bytes(content)
    return filename


def fetch_arxiv_metadata(arxiv_id: str) -> PaperData | None:
    import xml.etree.ElementTree as ET

    clean_id = arxiv_id.strip()
    if clean_id.startswith("http"):
        clean_id = clean_id.split("/abs/")[-1].split("?")[0]
    clean_id = re.sub(r"v\d+$", "", clean_id)

    url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
    try:
        resp = httpx.get(url, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(resp.text)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return None

    title = entry.findtext("atom:title", "", ns).replace("\n", " ").strip()
    if not title or "Error" in title:
        return None

    abstract = entry.findtext("atom:summary", "", ns).replace("\n", " ").strip()
    authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
    categories = [c.get("term", "") for c in entry.findall("atom:category", ns) if c.get("term")]

    pdf_url = None
    for link in entry.findall("atom:link", ns):
        if link.get("type") == "application/pdf":
            pdf_url = link.get("href")
            break

    pub_text = entry.findtext("atom:published", "", ns)
    from datetime import datetime
    published = None
    if pub_text:
        published = datetime.fromisoformat(pub_text.replace("Z", "+00:00"))

    return PaperData(
        title=title,
        abstract=abstract or None,
        authors=authors,
        year=published.year if published else None,
        arxiv_id=clean_id,
        pdf_url=pdf_url,
        abs_url=f"https://arxiv.org/abs/{clean_id}",
        categories=categories,
        source="arxiv",
        published_date=published,
    )


def download_pdf(url: str) -> bytes | None:
    try:
        resp = httpx.get(url, timeout=60.0, follow_redirects=True)
        resp.raise_for_status()
        if len(resp.content) < 1000:
            return None
        return resp.content
    except httpx.HTTPError:
        return None


def fetch_doi_metadata(doi: str) -> PaperData | None:
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = httpx.get(url, timeout=15.0, headers={"Accept": "application/json"})
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    data = resp.json().get("message", {})
    title_parts = data.get("title", [])
    title = title_parts[0] if title_parts else None
    if not title:
        return None

    authors = []
    for a in data.get("author", []):
        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
        if name:
            authors.append(name)

    venue = None
    containers = data.get("container-title", [])
    if containers:
        venue = containers[0]

    year = None
    date_parts = data.get("published", {}).get("date-parts", [[]])
    if date_parts and date_parts[0]:
        year = date_parts[0][0]

    pdf_url = None
    for link in data.get("link", []):
        if link.get("content-type") == "application/pdf":
            pdf_url = link.get("URL")
            break

    return PaperData(
        title=title,
        abstract=None,
        authors=authors,
        venue=venue,
        year=year,
        doi=doi,
        pdf_url=pdf_url,
        source="doi",
    )
