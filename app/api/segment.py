from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.segment import Segment, SegmentRequest, Question

router = APIRouter()

@router.post("/segments", response_model=List[Segment])
async def get_segments(request: SegmentRequest):
    # TODO: Integration with AI services to analyze video
    return [
        Segment(
            id="seg_1",
            startTime=0,
            endTime=120,
            title="Introduction",
            questions=[
                Question(
                    question="What is this video about?",
                    options=["Introduction", "Conclusion", "Middle"],
                    correct_answer="Introduction"
                )
            ]
        )
    ]
