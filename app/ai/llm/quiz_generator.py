import json
import re
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


# =========================
# Model setup
# =========================

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL,
    use_auth_token=HF_TOKEN
)

tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    offload_folder="offload"
)


model.eval()


# =========================
# Prompts
# =========================

SYSTEM_PROMPT = (
    "You are a strict JSON generator.\n"
    "Rules:\n"
    "- Output ONLY valid JSON\n"
    "- No explanations\n"
    "- No markdown\n"
    "- Double quotes only\n"
    "- No trailing commas\n"
    "- Follow the schema EXACTLY\n"
    "Schema:\n"
    "{{\n"
    "  \"topic_title\": string,\n"
    "  \"short_summary\": string,\n"
    "  \"keywords\": [string, string, string, string, string],\n"
    "  \"quiz\": [\n"
    "    {{\n"
    "      \"type\": \"multiple_choice\",\n"
    "      \"question\": string,\n"
    "      \"options\": [string, string, string, string],\n"
    "      \"correct_answer\": number\n"
    "    }},\n"
    "    {{\n"
    "      \"type\": \"true_false\",\n"
    "      \"question\": string,\n"
    "      \"correct_answer\": boolean\n"
    "    }},\n"
    "    {{\n"
    "      \"type\": \"short_answer\",\n"
    "      \"question\": string,\n"
    "      \"correct_answer\": null\n"
    "    }}\n"
    "  ]\n"
    "}}"
)

USER_PROMPT_TEMPLATE = """
Generate a quiz from the transcript.

Transcript:
{text}
"""


# =========================
# JSON parsing
# =========================

def parse_json(text: str) -> dict:
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

    # Check for markdown code block
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

    # Fallback: extract JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or start > end:
        raise ValueError("No JSON object found in LLM output")

    payload = text[start:end + 1]

    # Clean up common issues
    payload = re.sub(r",\s*([}\]])", r"\1", payload)  # Remove trailing commas

    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        # Debug: print the payload for troubleshooting
        print(f"Failed to parse JSON payload: {payload}")
        raise ValueError(f"Invalid JSON returned by LLM: {e}") from e


# =========================
# Public API
# =========================

def generate_quiz_for_segment(segment: dict) -> dict:
    """
    Input:
        segment = {
            "id": str,
            "start_time": float,
            "end_time": float,
            "text": str
        }

    Output:
        Parsed quiz JSON (dict)
    """

    if not segment.get("text"):
        raise ValueError("Segment text is empty")

    user_prompt = USER_PROMPT_TEMPLATE.format(text=segment["text"])

    prompt = tokenizer.apply_chat_template(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        tokenize=False
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True
    ).to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=500,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(output[0], skip_special_tokens=True)

    print(f"Quiz LLM Response: {response}")

    return parse_json(response)
