from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: str

class Segment(BaseModel):
    id: str
    startTime: float
    endTime: float
    title: str
    questions: List[Question]

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
    locked: bool = False


class SegmentQuizResponse(BaseModel):
    video_id: int
    segment_id: int
    quiz: List[Any]


class SegmentItem(BaseModel):
    id: int
    start_time: str
    end_time: str
    topic_title: str
    short_summary: str
    keywords: List[str]
    text: str
    quiz: List[Any] | None = None
