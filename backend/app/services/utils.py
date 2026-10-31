import json
import re


def parse_json_object(raw: str) -> dict:
    """Turn the AI's answer into a Python dict.

    LLMs sometimes wrap JSON in ```json fences or add a sentence before it,
    even when told not to. So we strip fences, then keep only the part between
    the first "{" and the last "}".
    """
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in AI response")

    data = json.loads(text[start : end + 1])  # JSONDecodeError is a ValueError
    if not isinstance(data, dict):
        raise ValueError("AI response is not a JSON object")
    return data


def clean_list(value, limit: int = 25) -> list:
    """Make sure we always end up with a short list of unique, non-empty strings."""
    if not isinstance(value, list):
        return []
    seen = set()
    result = []
    for item in value:
        if not isinstance(item, str):
            continue
        item = item.strip()
        if not item or item.lower() in seen:
            continue
        seen.add(item.lower())
        result.append(item)
        if len(result) >= limit:
            break
    return result


def clean_str(value):
    """Return a stripped string, or None for empty / 'null' values."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower() in ("", "null", "none", "n/a"):
        return None
    return value
