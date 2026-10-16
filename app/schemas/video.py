from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field


class VideoCreateResponse(BaseModel):
    video_id: int
    status: str


class SegmentResponse(BaseModel):
    id: int
    start_time: str
    end_time: str
    topic_title: str
    short_summary: str
    keywords: List[str]


class QuizResponse(BaseModel):
    topic_title: str
    short_summary: str
    keywords: List[str]
    quiz: List[Dict[str, Any]]


class AnswerRequest(BaseModel):
    question_index: int = Field(ge=0)
    answer: Union[str, int, bool]


class AnswerResponse(BaseModel):
    correct: bool
    feedback: str
