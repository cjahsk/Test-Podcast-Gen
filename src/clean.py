from __future__ import annotations

import re

from src.utils import clean_text


def normalize_source_text(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    return text.strip()


def normalize_script_text(text: str) -> str:
    text = clean_text(text)
    text = text.replace("•", "-")
    return text.strip()
