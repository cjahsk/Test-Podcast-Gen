from __future__ import annotations

import re

from src.models import ValidationResult
from src.utils import count_words

SECTION_HINTS = {
    "intro": ["today", "welcome", "quick"],
    "product_overview": ["product", "brand", "this is", "overview"],
    "key_selling_points": ["key", "benefit", "selling", "advantage", "stands out"],
    "serve_or_usage_suggestions": ["serve", "pair", "use", "ideal", "suggest"],
    "why_it_matters": ["matters", "helps", "for your", "in outlet", "for accounts"],
    "close": ["thanks", "next time", "in summary", "to close", "bottom line"],
}

PLACEHOLDER_PATTERNS = [
    r"insert\s+.*here",
    r"\[.*?\]",
    r"<.*?>",
]

HALLUCINATION_PATTERNS = [
    r"best\s+in\s+the\s+world",
    r"number\s+one\s+globally",
    r"unbeatable",
    r"guaranteed\s+results",
]


def validate_script(
    script: str,
    min_words: int,
    max_words: int,
    allow_missing_sections: bool,
    allow_bullets: bool,
) -> ValidationResult:
    issues: list[str] = []
    warnings: list[str] = []

    word_count = count_words(script)
    if word_count < min_words:
        issues.append(f"Word count is too low: {word_count} < {min_words}.")
    if word_count > max_words:
        issues.append(f"Word count is too high: {word_count} > {max_words}.")

    if re.search(r"^\s*#{1,6}\s+", script, flags=re.MULTILINE):
        issues.append("Script contains markdown headings.")

    if not allow_bullets and re.search(r"^\s*([-*]|\d+\.)\s+", script, flags=re.MULTILINE):
        issues.append("Script contains bullet points or numbered lists.")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, script, flags=re.IGNORECASE):
            issues.append("Script contains placeholder-style text.")
            break

    for pattern in HALLUCINATION_PATTERNS:
        if re.search(pattern, script, flags=re.IGNORECASE):
            warnings.append("Script includes potentially unsupported superlative phrasing.")
            break

    if not allow_missing_sections:
        missing_sections = _find_missing_sections(script)
        if missing_sections:
            issues.append(f"Script may be missing sections: {', '.join(missing_sections)}")

    if re.search(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\u024F]", script):
        warnings.append("Script contains uncommon characters that may affect speech rendering.")

    return ValidationResult(passed=len(issues) == 0, issues=issues, warnings=warnings)


def _find_missing_sections(script: str) -> list[str]:
    lower = script.lower()
    missing: list[str] = []
    for section, hints in SECTION_HINTS.items():
        if not any(hint in lower for hint in hints):
            missing.append(section)
    return missing
