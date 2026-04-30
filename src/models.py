from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RunMetadata:
    input_filename: str
    run_timestamp_utc: str
    output_dir: str
    text_model: str
    tts_model: str
    tts_voice: str
    script_word_count: int
    estimated_minutes: float
    validation_passed: bool
    warnings: list[str] = field(default_factory=list)
    token_usage: dict[str, Any] = field(default_factory=dict)
    repaired: bool = False
    error: str | None = None


@dataclass
class ProcessResult:
    input_file: Path
    success: bool
    output_dir: Path | None = None
    error: str | None = None
