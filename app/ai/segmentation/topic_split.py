from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering


def split_into_chunks(segments: List[Dict], chunk_size: int = 10) -> List[Dict]:
    """
    Convert Whisper segments into fixed-size chunks for embedding.
    Each chunk contains combined text and time range.
    """
    chunks = []
    for i in range(0, len(segments), chunk_size):
        chunk = segments[i:i + chunk_size]
        start = chunk[0]["start"]
        end = chunk[-1]["end"]
        text = " ".join([s["text"] for s in chunk]).strip()
        chunks.append({"start": start, "end": end, "text": text})
    return chunks


def segment_topics(chunks: List[Dict], n_topics: int = 5) -> List[Dict]:
    """
    Cluster chunks into topics using embeddings.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)

    clustering = AgglomerativeClustering(n_clusters=n_topics)
    labels = clustering.fit_predict(embeddings)

    topics = {}
    for idx, label in enumerate(labels):
        if label not in topics:
            topics[label] = {"start": chunks[idx]["start"], "end": chunks[idx]["end"], "texts": []}
        topics[label]["texts"].append(chunks[idx]["text"])
        topics[label]["end"] = max(topics[label]["end"], chunks[idx]["end"])

    result = []
    for label, data in topics.items():
        result.append({
            "start_time": seconds_to_hhmmss(data["start"]),
            "end_time": seconds_to_hhmmss(data["end"]),
            "topic_title": "Topic " + str(label + 1),
            "short_summary": " ".join(data["texts"])[:250] + "...",
            "keywords": extract_keywords(" ".join(data["texts"]))
        })

    result.sort(key=lambda x: x["start_time"])
    return result


def seconds_to_hhmmss(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def extract_keywords(text: str, top_k: int = 6) -> List[str]:
    """
    Simple keyword extraction using frequency.
    """
    words = [w.lower() for w in text.split() if len(w) > 3]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:top_k]]
