from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.video import Video
from app.schemas.video import VideoCreateResponse
from app.services.video_service import process_video
from pathlib import Path
import uuid

router = APIRouter(prefix="/video", tags=["video"])

UPLOAD_DIR = Path("data/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
