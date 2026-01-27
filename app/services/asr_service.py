from app.ai.whisper.transcriber import transcribe


def transcribe_video(video_id: int, audio_path: str):
    return transcribe(audio_path)
