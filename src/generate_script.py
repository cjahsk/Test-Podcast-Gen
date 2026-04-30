from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from src.utils import clean_text


def _load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _usage_to_dict(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if not usage:
        return {}
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def generate_script(
    client: OpenAI,
    model: str,
    source_text: str,
    system_prompt_path: Path,
    min_words: int,
    max_words: int,
    retries: int,
) -> tuple[str, dict[str, Any]]:
    system_prompt = _load_prompt(system_prompt_path)
    user_prompt = (
        f"Source material:\n{source_text}\n\n"
        f"Write one script between {min_words} and {max_words} words."
    )
    response = _response_with_retry(
        client=client,
        model=model,
        instructions=system_prompt,
        user_input=user_prompt,
        retries=retries,
    )
    return clean_text(response.output_text), _usage_to_dict(response)


def repair_script(
    client: OpenAI,
    model: str,
    source_text: str,
    draft_script: str,
    issues: list[str],
    repair_prompt_path: Path,
    min_words: int,
    max_words: int,
    retries: int,
) -> tuple[str, dict[str, Any]]:
    instructions = _load_prompt(repair_prompt_path)
    issue_lines = "\n".join(f"- {i}" for i in issues)
    user_input = (
        f"Source material:\n{source_text}\n\n"
        f"Draft script:\n{draft_script}\n\n"
        f"Validation issues:\n{issue_lines}\n\n"
        f"Please repair this to be between {min_words} and {max_words} words."
    )
    response = _response_with_retry(
        client=client,
        model=model,
        instructions=instructions,
        user_input=user_input,
        retries=retries,
    )
    return clean_text(response.output_text), _usage_to_dict(response)


def _response_with_retry(
    client: OpenAI,
    model: str,
    instructions: str,
    user_input: str,
    retries: int,
):
    delay = 1.0
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return client.responses.create(
                model=model,
                instructions=instructions,
                input=user_input,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"OpenAI script request failed after retries: {last_error}")
