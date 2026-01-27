from pydantic import BaseModel

class QuizResult(BaseModel):
    segment_id: str
    success: bool
    timestamp: int


class SegmentAnswerItem(BaseModel):
    question_index: int
    answer: str | int | bool | None


class SegmentAnswerRequest(BaseModel):
    video_id: int
    user_id: str
    answers: list[SegmentAnswerItem]


class SegmentAnswerResponse(BaseModel):
    video_id: int
    segment_id: int
    is_correct: bool
