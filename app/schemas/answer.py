from pydantic import BaseModel

class QuizResult(BaseModel):
    segment_id: str
    success: bool
    timestamp: int
