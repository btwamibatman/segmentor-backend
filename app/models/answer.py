from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class SegmentAnswer(Base):
    __tablename__ = "segment_answers"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    segment_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    answer_payload = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
