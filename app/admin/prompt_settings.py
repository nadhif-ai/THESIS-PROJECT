"""One global conversational prompt, stored in the existing private settings table."""

import unicodedata

from app.admin import store
from app.backend.prompt_template import DEFAULT_CONVERSATIONAL_PROMPT, prompt_snapshot

SETTING_KEY = "global_conversational_prompt"
MAX_PROMPT_LENGTH = 12000


def validate(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter conversational instructions before saving.")
    if len(text) > MAX_PROMPT_LENGTH:
        raise ValueError(f"Use at most {MAX_PROMPT_LENGTH:,} characters.")
    if any(unicodedata.category(c) == "Cs" or (unicodedata.category(c) == "Cc" and c not in "\n\r\t") for c in text):
        raise ValueError("Remove unsupported control characters.")
    return text.strip()


def active_snapshot():
    # Read per request, so separate workers observe a committed save without a cache TTL.
    return prompt_snapshot(validate(store.get_setting(SETTING_KEY, DEFAULT_CONVERSATIONAL_PROMPT)))


def editor():
    snapshot = active_snapshot()
    return {"prompt": snapshot["instructions"], "default_prompt": DEFAULT_CONVERSATIONAL_PROMPT,
            "prompt_sha256": snapshot["sha256"], "max_length": MAX_PROMPT_LENGTH}


def save(text):
    text = validate(text)
    store.set_setting(SETTING_KEY, text)
    snapshot = prompt_snapshot(text)
    return {"prompt": text, "default_prompt": DEFAULT_CONVERSATIONAL_PROMPT,
            "prompt_sha256": snapshot["sha256"], "max_length": MAX_PROMPT_LENGTH}
