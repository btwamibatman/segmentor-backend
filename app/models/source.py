from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class VideoSource(Base):
    __tablename__ = "video_sources"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    source_url = Column(String, nullable=False, index=True, unique=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
