import json
import re
import os
import importlib.util
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

token = os.getenv("HUGGINGFACE_TOKEN")
MODEL = "meta-llama/Llama-2-7b-chat-hf"

_has_bitsandbytes = importlib.util.find_spec("bitsandbytes") is not None

bnb_config = None
if _has_bitsandbytes:
  bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
  )

tokenizer = AutoTokenizer.from_pretrained(
    MODEL,
    use_auth_token=token
)

tokenizer.pad_token = tokenizer.eos_token

model_kwargs = {
  "device_map": "auto",
  "offload_folder": "offload",
}

if bnb_config is not None:
  model_kwargs["quantization_config"] = bnb_config
elif torch.cuda.is_available():
  model_kwargs["torch_dtype"] = torch.float16

model = AutoModelForCausalLM.from_pretrained(
  MODEL,
  **model_kwargs
)

SYSTEM_PROMPT = """
You are a strict JSON generator.

Rules:
- Output ONLY valid JSON
- No explanations
- No markdown
- Double quotes only
- No trailing commas
- No comments
- Follow the schema EXACTLY
"""

USER_PROMPT_TEMPLATE = """
Generate a quiz from the transcript.

Schema:

{
  "topic_title": string,
  "short_summary": string,
  "keywords": [string, string, string, string, string],
  "quiz": [
    {
      "type": "multiple_choice",
      "question": string,
      "options": [string, string, string, string],
      "correct_answer": number
    }
    | {
      "type": "true_false",
      "question": string,
      "correct_answer": boolean
    }
    | {
      "type": "short_answer",
      "question": string,
      "correct_answer": null
    }
  ]
}

Transcript:
{text}
"""

def parse_json(text: str):
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    payload = text[start:end + 1]

    payload = re.sub(r",\s*([}\]])", r"\1", payload)

    return json.loads(payload)


def generate_quiz_for_segment(segment):
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

    output = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=False,
        temperature=0.0,
        top_p=1.0,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(output[0], skip_special_tokens=True)

    return parse_json(response)