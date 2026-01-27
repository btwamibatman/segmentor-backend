from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    status = Column(String, default="queued", nullable=False)

    transcript = Column(Text, nullable=True)
    segments = Column(Text, nullable=True)
    quizzes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
