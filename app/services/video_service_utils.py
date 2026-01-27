import subprocess
import os
from pathlib import Path
import yt_dlp

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

def download_audio_from_url(url: str, output_stem: str) -> str:
    """
    Download best audio track from a URL (e.g., YouTube) and save as MP3.
    output_stem should be a full path without extension.
    """
    Path(output_stem).parent.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_stem}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    final_path = f"{output_stem}.mp3"
    if not os.path.exists(final_path):
        raise FileNotFoundError(f"Downloaded audio not found: {final_path}")

    return final_path
