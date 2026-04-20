from __future__ import annotations

import time
from pathlib import Path

from openai import OpenAI


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
            with client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=script,
                format="mp3",
            ) as response:
                response.stream_to_file(str(output_path))
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"OpenAI TTS request failed after retries: {last_error}")
