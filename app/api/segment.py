import json
import os
from typing import List, Any

from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.answer import SegmentAnswer
from app.models.video import Video
from app.models.source import VideoSource
from app.schemas.answer import SegmentAnswerRequest, SegmentAnswerResponse
from app.schemas.segment import SegmentItem, SegmentQuizResponse, SegmentRequest
from app.schemas.video import VideoCreateResponse
from app.services.video_service import process_video_url

router = APIRouter(tags=["segments"])


def _require_access_token(x_access_token: str | None = Header(default=None)):
    token = os.getenv("ACCESS_TOKEN")
    if token and x_access_token != token:
        raise HTTPException(status_code=401, detail="Invalid access token")


def _load_json(text_value: str | None) -> Any:
    if not text_value:
        return None
    try:
        return json.loads(text_value)
    except json.JSONDecodeError:
        return None


def _build_segment_items(video: Video, locked_map: dict[int, bool]) -> List[SegmentItem]:
    segments = _load_json(video.segments) or []
    quizzes = _load_json(video.quizzes) or []

    items: List[SegmentItem] = []
    for idx, seg in enumerate(segments, start=1):
        quiz_block = quizzes[idx - 1] if idx - 1 < len(quizzes) else None
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
                locked=locked_map.get(idx, False),
            )
        )

    return items


def _get_video(db: Session, video_id: int) -> Video:
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "done":
        raise HTTPException(status_code=409, detail=f"Video status is '{video.status}'")
    return video


def _get_video_by_url(db: Session, video_url: str) -> Video | None:
    source = db.query(VideoSource).filter(VideoSource.source_url == video_url).first()
    if not source:
        return None
    return db.query(Video).filter(Video.id == source.video_id).first()


def _locked_map(db: Session, video_id: int, user_id: str, total: int) -> dict[int, bool]:
    if total <= 0:
        return {}

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

    locked: dict[int, bool] = {}
    for seg_id in range(1, total + 1):
        if seg_id == 1:
            locked[seg_id] = False
            continue
        locked[seg_id] = not all(prev in correct_segments for prev in range(1, seg_id))
    return locked


def _get_segment_quiz(video: Video, segment_id: int) -> List[Any]:
    quizzes = _load_json(video.quizzes) or []
    if segment_id < 1 or segment_id > len(quizzes):
        raise HTTPException(status_code=404, detail="Segment quiz not found")
    quiz_block = quizzes[segment_id - 1]
    if isinstance(quiz_block, dict):
        return quiz_block.get("quiz", [])
    return quiz_block


@router.post("/segments", response_model=VideoCreateResponse)
def create_segments_job(
    payload: SegmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(_require_access_token),
):
    if not payload.video_url:
        raise HTTPException(status_code=400, detail="video_url is required")

    existing_video = _get_video_by_url(db, payload.video_url)
    if existing_video:
        return VideoCreateResponse(video_id=existing_video.id, status=existing_video.status)

    video = Video(file_path="", status="downloading")
    db.add(video)
    db.commit()
    db.refresh(video)

    db.add(VideoSource(video_id=video.id, source_url=payload.video_url))
    db.commit()

    if background_tasks is not None:
        background_tasks.add_task(process_video_url, video.id, payload.video_url)
    else:
        process_video_url(video.id, payload.video_url)

    return VideoCreateResponse(video_id=video.id, status=video.status)


@router.get("/segments", response_model=List[SegmentItem])
def get_segments(
    background_tasks: BackgroundTasks,
    video_id: int | None = None,
    video_url: str | None = None,
    url: str | None = None,
    user_id: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(_require_access_token),
):
    user = user_id or "anonymous"
    target_url = video_url or url

    if target_url:
        video = _get_video_by_url(db, target_url)
        if not video:
            video = Video(file_path="", status="downloading")
            db.add(video)
            db.commit()
            db.refresh(video)

            db.add(VideoSource(video_id=video.id, source_url=target_url))
            db.commit()

            if background_tasks is not None:
                background_tasks.add_task(process_video_url, video.id, target_url)
            else:
                process_video_url(video.id, target_url)

            return []
    elif video_id is not None:
        video = _get_video(db, video_id)
    else:
        raise HTTPException(status_code=400, detail="video_id or video_url is required")

    if target_url and video.status != "done":
        return []
    if not target_url and video.status != "done":
        raise HTTPException(status_code=409, detail=f"Video status is '{video.status}'")

    segments = _load_json(video.segments) or []
    locked = _locked_map(db, video.id, user, len(segments))
    return _build_segment_items(video, locked)


@router.get("/segment/{segment_id}/quiz", response_model=SegmentQuizResponse)
def get_segment_quiz(
    segment_id: int,
    video_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(_require_access_token),
):
    video = _get_video(db, video_id)
    segments = _load_json(video.segments) or []
    locked = _locked_map(db, video_id, user_id, len(segments))
    if locked.get(segment_id, True):
        raise HTTPException(status_code=403, detail="Segment is locked")

    quiz = _get_segment_quiz(video, segment_id)
    return SegmentQuizResponse(video_id=video_id, segment_id=segment_id, quiz=quiz)


@router.get("/setment/{segment_id}", response_model=SegmentQuizResponse, include_in_schema=False)
def get_segment_quiz_alias(
    segment_id: int,
    video_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(_require_access_token),
):
    return get_segment_quiz(segment_id, video_id, user_id, db, _)


@router.post("/segment/{segment_id}/answer", response_model=SegmentAnswerResponse)
def submit_segment_answer(
    segment_id: int,
    payload: SegmentAnswerRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_require_access_token),
):
    if payload.video_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid video_id")
    if not payload.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    video = _get_video(db, payload.video_id)
    segments = _load_json(video.segments) or []
    locked = _locked_map(db, payload.video_id, payload.user_id, len(segments))
    if locked.get(segment_id, True):
        raise HTTPException(status_code=403, detail="Segment is locked")

    quiz = _get_segment_quiz(video, segment_id)
    is_correct = True

    for answer in payload.answers:
        if answer.question_index < 0 or answer.question_index >= len(quiz):
            is_correct = False
            continue

        question = quiz[answer.question_index]
        correct_answer = question.get("correct_answer") if isinstance(question, dict) else None
        if correct_answer is None:
            is_correct = False
            continue

        if answer.answer != correct_answer:
            is_correct = False

    record = SegmentAnswer(
        video_id=payload.video_id,
        segment_id=segment_id,
        user_id=payload.user_id,
        is_correct=is_correct,
        answer_payload=json.dumps(payload.model_dump(), ensure_ascii=False),
    )
    db.add(record)
    db.commit()

    return SegmentAnswerResponse(
        video_id=payload.video_id,
        segment_id=segment_id,
        is_correct=is_correct,
    )
