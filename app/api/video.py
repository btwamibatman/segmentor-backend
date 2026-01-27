import json
import os
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.answer import SegmentAnswer
from app.models.video import Video
from app.schemas.segment import SegmentItem
from app.schemas.video import VideoCreateResponse
from app.services.video_service import process_video
from pathlib import Path
import uuid

router = APIRouter(prefix="/video", tags=["video"])

UPLOAD_DIR = Path("data/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _require_access_token(x_access_token: str | None = Header(default=None)):
    token = os.getenv("ACCESS_TOKEN")
    if token and x_access_token != token:
        raise HTTPException(status_code=401, detail="Invalid access token")


def _load_json(text_value: str | None):
    if not text_value:
        return None
    try:
        return json.loads(text_value)
    except json.JSONDecodeError:
        return None

@router.post("/upload", response_model=VideoCreateResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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

    background_tasks.add_task(process_video, video.id)

    return VideoCreateResponse(video_id=video.id, status=video.status)


@router.get("/{video_id}/segments", response_model=list[SegmentItem])
def get_video_segments(
    video_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(_require_access_token),
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "done":
        raise HTTPException(status_code=409, detail=f"Video status is '{video.status}'")

    segments = _load_json(video.segments) or []
    quizzes = _load_json(video.quizzes) or []

    correct_segments = {
        row.segment_id
        for row in db.query(SegmentAnswer)
        .filter(
            SegmentAnswer.video_id == video_id,
            SegmentAnswer.user_id == user_id,
            SegmentAnswer.is_correct.is_(True),
        )
        .all()
    }

    items: list[SegmentItem] = []
    for idx, seg in enumerate(segments, start=1):
        quiz_block = quizzes[idx - 1] if idx - 1 < len(quizzes) else None
        locked = idx != 1 and not all(prev in correct_segments for prev in range(1, idx))

        items.append(
            SegmentItem(
                id=idx,
                start_time=seg.get("start_time", "00:00:00"),
                end_time=seg.get("end_time", "00:00:00"),
                topic_title=seg.get("topic_title", ""),
                short_summary=seg.get("short_summary", ""),
                keywords=seg.get("keywords", []),
                text=seg.get("text", ""),
                quiz=(quiz_block.get("quiz") if isinstance(quiz_block, dict) else None),
                locked=locked,
            )
        )

    return items
