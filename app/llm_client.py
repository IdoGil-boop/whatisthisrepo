"""Nebius Token Factory LLM client — model selection, prompting, JSON validation."""

from __future__ import annotations

import json
import logging
from typing import Optional

import openai
from openai import AsyncOpenAI

import app.config as cfg
from app.config import LLM_TIMEOUT, MODEL_TIERS, NEBIUS_API_KEY
from app.models import LLMError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"

SYSTEM_PROMPT = (
    "You are a code repository analyst. Given a REPO DIGEST, produce a JSON object "
    "with exactly three keys:\n"
    '  "summary": a concise human-readable description of what the project does,\n'
    '  "technologies": an array of strings listing the main languages, frameworks, '
    "and libraries used,\n"
    '  "structure": a brief description of the project layout.\n\n'
    "Rules:\n"
    "- Output ONLY valid JSON. No markdown fences, no extra keys, no commentary.\n"
    "- Use only the provided digest. If uncertain, say 'Unknown' rather than guessing.\n"
)

REPAIR_PROMPT = (
    "Your previous response was not valid JSON matching the required schema. "
    "Return ONLY valid JSON with keys: summary (string), technologies (array of strings), "
    "structure (string). No markdown, no extra keys."
)


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------


def select_model(digest_size: int) -> str:
    """Pick the cheapest model that fits the digest, or use env override."""
    if cfg.NEBIUS_MODEL:
        return cfg.NEBIUS_MODEL
    for threshold, model in MODEL_TIERS:
        if digest_size < threshold:
            return model
    # Fallback to largest
    return MODEL_TIERS[-1][1]


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = {"summary", "technologies", "structure"}


def _parse_and_validate(raw: str) -> Optional[dict]:
    """Parse JSON string and validate schema. Returns dict or None on failure."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if not _REQUIRED_KEYS.issubset(data.keys()):
        return None
    if not isinstance(data["summary"], str):
        return None
    if not isinstance(data["technologies"], list):
        return None
    if not all(isinstance(t, str) for t in data["technologies"]):
        return None
    if not isinstance(data["structure"], str):
        return None
    return data


# ---------------------------------------------------------------------------
# Summarize
# ---------------------------------------------------------------------------


async def summarize(digest: str) -> dict:
    """Send digest to LLM, parse response, retry once on failure."""
    model = select_model(len(digest))
    client = AsyncOpenAI(base_url=_BASE_URL, api_key=NEBIUS_API_KEY)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": digest},
    ]

    logger.info("Calling LLM model=%s digest_chars=%d", model, len(digest))
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=2000,
            timeout=LLM_TIMEOUT,
        )
    except (openai.APIError, openai.APITimeoutError) as exc:
        raise LLMError(f"LLM provider error: {exc}") from exc

    if not resp.choices:
        raise LLMError("LLM returned no response choices")
    raw = resp.choices[0].message.content or ""
    result = _parse_and_validate(raw)
    if result is not None:
        return result

    # Retry once with repair prompt
    logger.warning("LLM response invalid, retrying with repair prompt")
    messages.append({"role": "assistant", "content": raw})
    messages.append({"role": "user", "content": REPAIR_PROMPT})

    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=2000,
            timeout=LLM_TIMEOUT,
        )
    except (openai.APIError, openai.APITimeoutError) as exc:
        raise LLMError(f"LLM provider error: {exc}") from exc

    if not resp.choices:
        raise LLMError("LLM returned no response choices")
    raw = resp.choices[0].message.content or ""
    result = _parse_and_validate(raw)
    if result is not None:
        return result

    raise LLMError("LLM failed to produce a valid summary after retry")
