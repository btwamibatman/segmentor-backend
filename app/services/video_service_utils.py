import subprocess
import os
from pathlib import Path
import shutil
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

    ffmpeg_location = None
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        # Common local install path used in this repo setup
        fallback_dir = Path(r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin")
        fallback_bin = fallback_dir / "ffmpeg.exe"
        if fallback_bin.exists():
            ffmpeg_bin = str(fallback_bin)

    if ffmpeg_bin:
        ffmpeg_dir = str(Path(ffmpeg_bin).parent)
        # Ensure child process can see ffmpeg/ffprobe
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}" + os.environ.get("PATH", "")
        ffmpeg_location = ffmpeg_bin

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_stem}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ffmpeg_location": ffmpeg_location,
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
