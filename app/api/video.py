import json
import uuid
from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi import Path as ApiPath
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.video import Video
from app.schemas.video import (
    AnswerRequest,
    AnswerResponse,
    QuizResponse,
    SegmentResponse,
    VideoCreateResponse,
)

router = APIRouter(prefix="/video", tags=["video"])

UPLOAD_DIR = Path("data/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_video_in_background(video_id: int) -> None:
    # Import lazily so API startup and non-processing endpoints do not load the
    # multi-gigabyte ML stack.
    from app.services.video_service import process_video

    process_video(video_id)


@router.post("/upload", response_model=VideoCreateResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix
    if ext.lower() not in [".mp4", ".mkv", ".mov", ".avi"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    filename = f"{uuid.uuid4()}{ext}"
    path = UPLOAD_DIR / filename

    with path.open("wb") as f:
        f.write(await file.read())

    video = Video(file_path=str(path), status="queued")
    db.add(video)
    db.commit()
    db.refresh(video)

    background_tasks.add_task(process_video_in_background, video.id)

    return VideoCreateResponse(video_id=video.id, status=video.status)


@router.get("/{video_id}/segments", response_model=List[SegmentResponse])
def get_segments(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or video.status != "done":
        raise HTTPException(status_code=404, detail="Video not found or not processed")

    segments = json.loads(video.segments)
    return [SegmentResponse(id=i, **seg) for i, seg in enumerate(segments)]


@router.get("/{video_id}/segment/{segment_index}/quiz", response_model=QuizResponse)
def get_quiz(
    video_id: int,
    segment_index: Annotated[int, ApiPath(ge=0)],
    db: Session = Depends(get_db),
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or video.status != "done":
        raise HTTPException(status_code=404, detail="Video not found or not processed")

    quizzes = json.loads(video.quizzes)
    segments = json.loads(video.segments)
    if segment_index >= len(quizzes):
        raise HTTPException(status_code=404, detail="Segment not found")

    quiz = quizzes[segment_index]
    segment = segments[segment_index]
    return QuizResponse(
        topic_title=segment["topic_title"],
        short_summary=segment["short_summary"],
        keywords=segment["keywords"],
        quiz=quiz["quiz"],
    )


@router.post(
    "/{video_id}/segment/{segment_index}/answer", response_model=AnswerResponse
)
def answer_quiz(
    video_id: int,
    segment_index: Annotated[int, ApiPath(ge=0)],
    answer: AnswerRequest,
    db: Session = Depends(get_db),
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or video.status != "done":
        raise HTTPException(status_code=404, detail="Video not found or not processed")

    quizzes = json.loads(video.quizzes)
    if segment_index >= len(quizzes):
        raise HTTPException(status_code=404, detail="Segment not found")

    quiz = quizzes[segment_index]["quiz"]
    if answer.question_index >= len(quiz):
        raise HTTPException(status_code=400, detail="Invalid question index")

    question = quiz[answer.question_index]
    correct = False
    if question["type"] == "multiple_choice":
        correct = answer.answer == question["correct_answer"]
    elif question["type"] == "true_false":
        correct = answer.answer == question["correct_answer"]
    elif question["type"] == "short_answer":
        # Short answers currently have no reference answer, so accept any response.
        correct = True

    feedback = "Correct!" if correct else "Incorrect, please review the segment."

    return AnswerResponse(correct=correct, feedback=feedback)
