from app.db.session import SessionLocal
from app.models.video import Video
from app.services.asr_service import transcribe_video
from app.services.video_service_utils import extract_audio

def process_video(video_id: int):
    db = SessionLocal()
    video = None

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        video.status = "processing"
        db.commit()

        audio_path = extract_audio(video.id, video.file_path)
        if audio_path is None:
            video.status = "no_audio"
            db.commit()
            return

        transcribe_video(video.id, audio_path)

        video.status = "done"
        db.commit()

    except Exception:
        db.rollback()
        if video:
            video.status = "failed"
            db.commit()
        raise

    finally:
        db.close()
