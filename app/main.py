from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.api.video import router as video_router
from app.api.segment import router as segment_router
from app.api.answer import router as answer_router
from app.core.logger import logger
from app.db.base import Base
from app.models import Video, SegmentAnswer, VideoSource
from app.db.session import engine

def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(
        title="SegMentor",
        version="0.1.0",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(video_router)
    app.include_router(segment_router)
    app.include_router(answer_router)

    return app

app = create_app()

@app.on_event("startup")
def on_startup():
    logger.info("Starting SegMentor API...")
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
