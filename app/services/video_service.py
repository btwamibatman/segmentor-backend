from app.db.session import SessionLocal
from app.models.video import Video
from app.services.asr_service import transcribe_video
from app.services.segment_service import segment_video
from app.services.video_service_utils import extract_audio
from app.ai.llm.quiz_generator import generate_quiz_for_segment
import json


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
            quiz = generate_quiz_for_segment(seg)
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
