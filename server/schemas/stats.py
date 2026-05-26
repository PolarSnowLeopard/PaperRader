from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_papers: int
    sources: dict[str, int]
    recent_week: int
    starred_count: int


class TrendPoint(BaseModel):
    date: str
    count: int


class TopicCount(BaseModel):
    topic: str
    count: int


class VenueCount(BaseModel):
    venue: str
    count: int


class TrendsResponse(BaseModel):
    daily: list[TrendPoint]


class TopicsResponse(BaseModel):
    topics: list[TopicCount]


class VenuesResponse(BaseModel):
    venues: list[VenueCount]
