from typing import List, Dict


def segment_video(video_id: int, transcript: dict) -> List[dict]:
    segments = transcript.get("segments", [])

    if not segments:
        return []

    # Minimal segmentation: one segment per 30 seconds
    result = []
    current = []
    start = segments[0]["start"]
    end = start

    for s in segments:
        if s["end"] - start > 30:
            result.append({
                "start_time": format_time(start),
                "end_time": format_time(end),
                "topic_title": "Topic",
                "short_summary": "Summary",
                "keywords": ["keyword"],
                "text": " ".join([x["text"] for x in current])
            })
            current = []
            start = s["start"]

        current.append(s)
        end = s["end"]

    if current:
        result.append({
            "start_time": format_time(start),
            "end_time": format_time(end),
            "topic_title": "Topic",
            "short_summary": "Summary",
            "keywords": ["keyword"],
            "text": " ".join([x["text"] for x in current])
        })

    return result


def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
