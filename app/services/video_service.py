from app.db.session import SessionLocal
from app.models.video import Video
from app.services.asr_service import transcribe_video
from app.services.segment_service import segment_video
from app.services.video_service_utils import extract_audio, download_video_from_url
import json


def _normalize_quiz(quiz_payload: dict, segment_text: str) -> dict:
    quiz_list = quiz_payload.get("quiz") if isinstance(quiz_payload, dict) else None
    if not isinstance(quiz_list, list):
        quiz_list = []

    # Ensure 3-5 questions
    while len(quiz_list) < 3:
        quiz_list.append(
            {
                "type": "short_answer",
                "question": "Summarize this segment in one sentence.",
                "correct_answer": None,
            }
        )

    quiz_payload["quiz"] = quiz_list[:5]
    return quiz_payload


def process_video(video_id: int):
    db = SessionLocal()
    video = None

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            print("Video not found")
            return

        video.status = "processing"
        db.commit()

        audio_path = extract_audio(video.id, video.file_path)
        if audio_path is None:
            video.status = "no_audio"
            db.commit()
            return

        # ASR
        transcript = transcribe_video(video.id, audio_path)
        print("ASR DONE:", transcript["language"], "segments:", len(transcript["segments"]))

        # Segmentation
        segments = segment_video(video.id, transcript)
        print("SEGMENTS:", len(segments))

        # Quiz generation
        quizzes = []
        for seg in segments:
            from app.ai.llm.quiz_generator import generate_quiz_for_segment

            quiz = generate_quiz_for_segment(seg)
            if isinstance(quiz, dict):
                quiz = _normalize_quiz(quiz, seg.get("text", ""))
            quizzes.append(quiz)
            print("QUIZ for segment", seg["start_time"], "->", seg["end_time"])
            print(quiz)

        # Save everything
        video.transcript = json.dumps(transcript, ensure_ascii=False)
        video.segments = json.dumps(segments, ensure_ascii=False)
        video.quizzes = json.dumps(quizzes, ensure_ascii=False)

        video.status = "done"
        db.commit()

    except Exception as e:
        db.rollback()
        if video:
            video.status = "failed"
            db.commit()
        raise e

    finally:
        db.close()


def process_video_url(video_id: int, video_url: str):
    db = SessionLocal()
    video = None

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            print("Video not found")
            return

        video.status = "downloading"
        db.commit()

        path = download_video_from_url(video_url)
        video.file_path = path
        video.status = "queued"
        db.commit()

        process_video(video.id)

    except Exception as e:
        db.rollback()
        if video:
            video.status = "failed"
            db.commit()
        raise e

    finally:
        db.close()
