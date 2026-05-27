"""
ACL Anthology collector for ACL, EMNLP, NAACL papers.

ACL Anthology provides a structured API at https://aclanthology.org/
"""

import re
import xml.etree.ElementTree as ET

import httpx

from paperader.collectors.base import BaseCollector, PaperData

# Mapping from conference keys to (xml_file, volume_id) tuples
# XML data: https://github.com/acl-org/acl-anthology/tree/master/data/xml
ANTHOLOGY_EVENTS = {
    "ACL2024": ("2024.acl", "long"),
    "ACL2023": ("2023.acl", "long"),
    "EMNLP2024": ("2024.emnlp", "main"),
    "EMNLP2023": ("2023.emnlp", "main"),
    "NAACL2024": ("2024.naacl", "long"),
    "NAACL2025": ("2025.naacl", "long"),
    "EACL2024": ("2024.eacl", "long"),
}

ANTHOLOGY_XML_BASE = "https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml"
ANTHOLOGY_URL = "https://aclanthology.org"


class AclAnthologyCollector(BaseCollector):
    def __init__(self, max_results: int = 200):
        self.max_results = max_results

    def collect(self, categories: list[str] | None = None, **kwargs) -> list[PaperData]:
        conference = kwargs.get("conference", "ACL2024")
        return self.get_conference_papers(conference)

    def get_conference_papers(self, conference_key: str) -> list[PaperData]:
        event = ANTHOLOGY_EVENTS.get(conference_key)
        if not event:
            return []

        xml_file, volume_id = event
        url = f"{ANTHOLOGY_XML_BASE}/{xml_file}.xml"

        try:
            response = httpx.get(url, timeout=60.0, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        return self._parse_xml(response.text, conference_key, volume_id)

    def _parse_xml(self, xml_text: str, conference_key: str, target_volume: str) -> list[PaperData]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        papers = []
        collection_id = root.get("id", "")

        for volume_elem in root.findall("volume"):
            if volume_elem.get("id") != target_volume:
                continue

            year_meta = volume_elem.find("meta/year")
            default_year = int(year_meta.text) if year_meta is not None and year_meta.text.isdigit() else None

            for paper_elem in volume_elem.findall("paper"):
                title_elem = paper_elem.find("title")
                if title_elem is None:
                    continue
                title = "".join(title_elem.itertext()).strip()
                if not title:
                    continue

                abstract_elem = paper_elem.find("abstract")
                abstract = "".join(abstract_elem.itertext()).strip() if abstract_elem is not None else None

                authors = []
                for author in paper_elem.findall("author"):
                    first = author.findtext("first", "")
                    last = author.findtext("last", "")
                    authors.append(f"{first} {last}".strip())

                year_text = paper_elem.findtext("year", "")
                year = int(year_text) if year_text.isdigit() else default_year

                paper_id = paper_elem.get("id", "")
                anthology_id = f"{collection_id}-{target_volume}.{paper_id}" if paper_id else None

                doi_text = paper_elem.findtext("doi")
                doi = doi_text if doi_text else None

                abs_url = f"{ANTHOLOGY_URL}/{anthology_id}" if anthology_id else None
                pdf_url = f"{ANTHOLOGY_URL}/{anthology_id}.pdf" if anthology_id else None

                venue = re.sub(r"(\d{4})", r" \1", conference_key)

                papers.append(
                    PaperData(
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        venue=venue,
                        year=year,
                        doi=doi,
                        pdf_url=pdf_url,
                        abs_url=abs_url,
                        source="acl_anthology",
                    )
                )

                if len(papers) >= self.max_results:
                    return papers

        return papers

    def list_available_conferences(self) -> list[str]:
        return list(ANTHOLOGY_EVENTS.keys())
