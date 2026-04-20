from __future__ import annotations

import time
from pathlib import Path

from openai import OpenAI


def _stream_tts_to_file(
    client: OpenAI,
    model: str,
    voice: str,
    script: str,
    output_path: Path,
) -> None:
    """
    Handle minor OpenAI SDK signature differences across versions.

    Some SDK versions expect `response_format`, while others may not accept
    an explicit format argument for this method.
    """
    base_kwargs = {
        "model": model,
        "voice": voice,
        "input": script,
    }

    # Try modern/most common signature first.
    try:
        with client.audio.speech.with_streaming_response.create(
            **base_kwargs,
            response_format="mp3",
        ) as response:
            response.stream_to_file(str(output_path))
        return
    except TypeError as exc:
        # Fall back for SDK variants that don't support response_format.
        if "response_format" not in str(exc):
            raise

    with client.audio.speech.with_streaming_response.create(**base_kwargs) as response:
        response.stream_to_file(str(output_path))


def text_to_speech(
    client: OpenAI,
    model: str,
    voice: str,
    script: str,
    output_path: Path,
    retries: int,
) -> None:
    delay = 1.0
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            _stream_tts_to_file(
                client=client,
                model=model,
                voice=voice,
                script=script,
                output_path=output_path,
            )
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"OpenAI TTS request failed after retries: {last_error}")
