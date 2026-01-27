from typing import List, Dict
import json
import re
import torch
from app.ai.llm import quiz_generator


SYSTEM_PROMPT_SEG = (
    "You are a strict JSON generator.\n"
    "Rules:\n"
    "- Output ONLY valid JSON\n"
    "- No explanations\n"
    "- No markdown\n"
    "- Double quotes only\n"
    "- No trailing commas\n"
    "- Follow the schema EXACTLY\n"
    "Schema:\n"
    "[\n"
    "  {{\n"
    "    \"start_time\": \"HH:MM:SS\",\n"
    "    \"end_time\": \"HH:MM:SS\",\n"
    "    \"topic_title\": \"string\",\n"
    "    \"short_summary\": \"string\",\n"
    "    \"keywords\": [\"string\"]\n"
    "  }}\n"
    "]"
)

SEGMENT_PROMPT_TEMPLATE = """
Segment the transcript into logical topics. Each segment should be a coherent topic block.

Transcript with timestamps:
{text}
"""


def parse_json(text: str) -> list:
    # Clean the response by taking only the last part after the last "system" or "user"
    parts = text.split("system")
    if len(parts) > 1:
        text = parts[-1].strip()
    parts = text.split("user")
    if len(parts) > 1:
        text = parts[-1].strip()

    text = text.strip()

    # First, try to parse the entire response as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Check for markdown code block (though unlikely for array)
    if "```json" in text:
        start = text.find("```json") + len("```json")
        end = text.find("```", start)
        if end == -1:
            end = len(text)
        payload = text[start:end].strip()
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            pass

    # Fallback: extract JSON array
    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1 or start > end:
        raise ValueError("No JSON array found in LLM output")

    payload = text[start:end + 1]

    payload = re.sub(r",\s*([}\]])", r"\1", payload)

    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON payload: {payload}")
        raise ValueError(f"Invalid JSON returned by LLM: {e}") from e


def segment_video(video_id: int, transcript: dict) -> List[dict]:
    segments = transcript.get("segments", [])

    if not segments:
        return []

    if quiz_generator.tokenizer is None or quiz_generator.model is None:
        return basic_segmentation(segments)

    # Prepare transcript text with timestamps
    text_with_times = "\n".join([f"[{format_time(s['start'])} - {format_time(s['end'])}] {s['text']}" for s in segments])

    user_prompt = SEGMENT_PROMPT_TEMPLATE.format(text=text_with_times)

    prompt = quiz_generator.tokenizer.apply_chat_template(
        [
            {"role": "system", "content": SYSTEM_PROMPT_SEG},
            {"role": "user", "content": user_prompt},
        ],
        tokenize=False
    )

    inputs = quiz_generator.tokenizer(
        prompt,
        return_tensors="pt",
        padding=True
    ).to(quiz_generator.model.device)

    with torch.no_grad():
        output = quiz_generator.model.generate(
            **inputs,
            max_new_tokens=800,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            eos_token_id=quiz_generator.tokenizer.eos_token_id,
            pad_token_id=quiz_generator.tokenizer.eos_token_id,
        )

    response = quiz_generator.tokenizer.decode(output[0], skip_special_tokens=True)

    print(f"Segmentation LLM Response: {response}")

    try:
        parsed_segments = parse_json(response)
    except ValueError:
        # Fallback to basic segmentation
        return basic_segmentation(segments)

    # Add text to each segment from transcript
    for seg in parsed_segments:
        start_sec = time_to_seconds(seg["start_time"])
        end_sec = time_to_seconds(seg["end_time"])
        seg_text = " ".join([s["text"] for s in segments if s["start"] < end_sec and s["end"] > start_sec])
        seg["text"] = seg_text

    return parsed_segments


def basic_segmentation(segments: List[Dict]) -> List[dict]:
    # Fallback: one segment per 30 seconds
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


def time_to_seconds(time_str: str) -> float:
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s
