from typing import List, Any
from pydantic import BaseModel

class SegmentRequest(BaseModel):
    video_url: str


class SegmentItem(BaseModel):
    id: int
    start_time: str
    end_time: str
    topic_title: str
    short_summary: str
    keywords: List[str]
    text: str
    quiz: List[Any] | None = None
    locked: bool = False


class SegmentQuizResponse(BaseModel):
    video_id: int
    segment_id: int
    quiz: List[Any]
