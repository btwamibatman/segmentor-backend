import subprocess
import os
import uuid
from pathlib import Path

def extract_audio(video_id: int, video_path: str) -> str | None:
    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            video_path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if not probe.stdout.strip():
        return None

    os.makedirs("data/audio", exist_ok=True)
    audio_path = f"data/audio/{video_id}.wav"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ac", "1",
            "-ar", "16000",
            audio_path
        ],
        check=True
    )

    return audio_path


def download_video_from_url(video_url: str) -> str:
    os.makedirs("data/videos", exist_ok=True)
    filename = f"{uuid.uuid4()}.mp4"
    output_path = Path("data/videos") / filename

    subprocess.run(
        [
            "yt-dlp",
            "-f",
            "mp4",
            "--no-playlist",
            "-o",
            str(output_path),
            video_url,
        ],
        check=True,
    )

    return str(output_path)
