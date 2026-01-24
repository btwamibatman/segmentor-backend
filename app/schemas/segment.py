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
