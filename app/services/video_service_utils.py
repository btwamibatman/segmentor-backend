import subprocess
import os

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
