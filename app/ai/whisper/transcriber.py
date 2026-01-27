import os
import torch
from faster_whisper import WhisperModel

# Use a single underscore for the global placeholder
_model_instance = None

def _load_model():
    global _model_instance
    if _model_instance is None:
        # Auto-detect hardware
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # use int8 for CPU, float16 for GPU
        compute_type = "float16" if device == "cuda" else "int8"
        
        # Initialize faster-whisper correctly
        _model_instance = WhisperModel("small", device=device, compute_type=compute_type)
    return _model_instance

def transcribe(audio_path: str) -> dict:
    if not os.path.exists(audio_path):
        return {"text": "", "segments": [], "language": None}

    model = _load_model()

    try:
        # faster-whisper returns a generator (segments) and an info object
        segments_generator, info = model.transcribe(
            audio_path, 
            beam_size=5,
            task="transcribe"
        )

        segments = []
        text_parts = []

        # You MUST iterate to actually perform the transcription
        for s in segments_generator:
            text_parts.append(s.text.strip())
            segments.append({
                "start": float(s.start),
                "end": float(s.end),
                "text": s.text.strip()
            })

        return {
            "text": " ".join(text_parts),
            "segments": segments,
            "language": info.language
        }

    except Exception as e:
        print(f"Transcription Error: {e}")
        return {"text": "", "segments": [], "language": None}