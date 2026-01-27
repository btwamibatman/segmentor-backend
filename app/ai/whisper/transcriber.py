import os
import torch
import whisper


_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = whisper.load_model("small", device=device)
    return _MODEL


def transcribe(audio_path: str) -> dict:
    if not os.path.exists(audio_path):
        return {
            "text": "",
            "segments": [],
            "language": None
        }

    model = _load_model()

    try:
        result = model.transcribe(
            audio_path,
            task="transcribe",
            verbose=False
        )
    except Exception:
        return {
            "text": "",
            "segments": [],
            "language": None
        }

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "text": seg["text"].strip()
        })

    return {
        "text": result.get("text", "").strip(),
        "segments": segments,
        "language": result.get("language")
    }
