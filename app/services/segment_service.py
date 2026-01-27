from typing import List, Dict

from app.ai.segmentation.topic_split import split_into_chunks, segment_topics


def segment_video(video_id: int, transcript: dict) -> List[dict]:
    segments = transcript.get("segments", [])

    if not segments:
        return []

    # Try semantic topic segmentation first
    try:
        chunks = split_into_chunks(segments, chunk_size=10)
        if len(chunks) >= 3:
            n_topics = min(max(2, len(chunks) // 3), 8)
            topics = segment_topics(chunks, n_topics=n_topics)
            if topics:
                return topics
    except Exception:
        pass

    # Fallback segmentation: one segment per 30 seconds
    result = []
    current = []
    start = segments[0]["start"]
    end = start

    for s in segments:
        if current and s["end"] - start > 30:
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
