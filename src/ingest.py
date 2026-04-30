from __future__ import annotations

from pathlib import Path

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx", ".csv"}


def list_supported_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        [
            p
            for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
        ]
    )


def resolve_target_files(input_dir: Path, filename: str | None, process_all: bool) -> list[Path]:
    if filename:
        target = input_dir / filename
        return [target] if target.exists() and target.is_file() else []
    if process_all or filename is None:
        return list_supported_files(input_dir)
    return []
