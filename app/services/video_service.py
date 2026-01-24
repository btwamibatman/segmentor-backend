from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.video import Video

def process_video(video_id: int):
    db: Session = next(get_db())
    video = db.query(Video).filter(Video.id == video_id).first()
    video.status = "processing"
    db.commit()

    # TODO: транскрипция, сегментация, квизы
    # пока просто фейковый процесс:
    video.status = "done"
    db.commit()