from sqlalchemy import or_
from sqlalchemy.orm import Query

from paperader.models.paper import Paper
from paperader.search.intent import SearchIntent


def build_query(base_query: Query, intent: SearchIntent) -> Query:
    q = base_query

    # Keyword filtering (OR across all keywords in title/abstract)
    if intent.keywords_sql:
        keyword_conditions = []
        for kw in intent.keywords_sql:
            pattern = f"%{kw}%"
            keyword_conditions.append(Paper.title.ilike(pattern))
            keyword_conditions.append(Paper.abstract.ilike(pattern))
        q = q.filter(or_(*keyword_conditions))

    # Year range
    if intent.year_min:
        q = q.filter(Paper.year >= intent.year_min)
    if intent.year_max:
        q = q.filter(Paper.year <= intent.year_max)

    # Venue filter
    if intent.venues:
        venue_conditions = [Paper.venue.ilike(f"%{v}%") for v in intent.venues]
        q = q.filter(or_(*venue_conditions))

    # Author filter (JSON array stored as text — use LIKE for SQLite compatibility)
    if intent.authors:
        author_conditions = []
        for author in intent.authors:
            author_conditions.append(Paper.authors.cast(str).ilike(f"%{author}%"))
        q = q.filter(or_(*author_conditions))

    return q
