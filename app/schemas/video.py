from pydantic import BaseModel
from typing import List, Dict, Any, Union

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
    question_index: int
    answer: Union[str, int, bool]

class AnswerResponse(BaseModel):
    correct: bool
    feedback: str