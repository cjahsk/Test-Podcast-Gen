from __future__ import annotations

import argparse
import traceback
from pathlib import Path

from openai import OpenAI

from src.clean import normalize_script_text, normalize_source_text
from src.config import load_config
from src.extract import extract_text
from src.generate_script import generate_script, repair_script
from src.ingest import resolve_target_files
from src.models import ProcessResult, RunMetadata
from src.tts import text_to_speech
from src.utils import (
    count_words,
    ensure_dir,
    estimate_minutes,
    get_logger,
    slugify,
    utc_timestamp,
    write_json,
    write_text,
)
from src.validate import validate_script


PROMPTS_DIR = Path("prompts")
SCRIPT_PROMPT = PROMPTS_DIR / "script_system_prompt.txt"
REPAIR_PROMPT = PROMPTS_DIR / "script_repair_prompt.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate podcast scripts + MP3 from local product docs.")
    parser.add_argument("--file", type=str, help="Single filename from input folder.")
    parser.add_argument("--all", action="store_true", help="Process all supported input files.")
    parser.add_argument("--voice", type=str, help="Override TTS voice from config.")
    parser.add_argument("--min-words", type=int, help="Override minimum word count.")
    parser.add_argument("--max-words", type=int, help="Override maximum word count.")
    return parser.parse_args()


def process_file(
    file_path: Path,
    client: OpenAI,
    cfg,
    voice: str,
    min_words: int,
    max_words: int,
) -> ProcessResult:
    ts = utc_timestamp()
    slug = slugify(file_path.stem)
    output_dir = ensure_dir(cfg.output_dir / f"{ts}_{slug}")
    log_path = output_dir / "run.log"
    logger = get_logger(f"run:{file_path.name}", logfile=log_path, level=cfg.log_level)

    logger.info("Processing input file: %s", file_path.name)

    try:
        raw_text = extract_text(file_path)
        cleaned_source = normalize_source_text(raw_text)
        if not cleaned_source:
            raise ValueError("No readable text was extracted from file.")

        write_text(output_dir / "source_text.txt", cleaned_source)
        logger.info("Saved cleaned source text.")

        draft_script, usage_gen = generate_script(
            client=client,
            model=cfg.openai_text_model,
            source_text=cleaned_source,
            system_prompt_path=SCRIPT_PROMPT,
            min_words=min_words,
            max_words=max_words,
            retries=cfg.max_retries,
        )
        draft_script = normalize_script_text(draft_script)
        write_text(output_dir / "podcast_script_draft.txt", draft_script)
        logger.info("Generated and saved draft script.")

        validation = validate_script(
            script=draft_script,
            min_words=min_words,
            max_words=max_words,
            allow_missing_sections=cfg.allow_missing_sections,
            allow_bullets=cfg.allow_bullets,
        )

        final_script = draft_script
        repaired = False
        usage_repair = {}

        if not validation.passed and cfg.enable_repair_pass:
            logger.warning("Draft failed validation. Trying repair pass...")
            repaired_script, usage_repair = repair_script(
                client=client,
                model=cfg.openai_text_model,
                source_text=cleaned_source,
                draft_script=draft_script,
                issues=validation.issues,
                repair_prompt_path=REPAIR_PROMPT,
                min_words=min_words,
                max_words=max_words,
                retries=cfg.max_retries,
            )
            repaired_script = normalize_script_text(repaired_script)
            write_text(output_dir / "podcast_script_repaired.txt", repaired_script)
            repaired = True

            validation = validate_script(
                script=repaired_script,
                min_words=min_words,
                max_words=max_words,
                allow_missing_sections=cfg.allow_missing_sections,
                allow_bullets=cfg.allow_bullets,
            )
            final_script = repaired_script

        if not validation.passed:
            logger.error("Validation failed after repair logic: %s", validation.issues)
            metadata = RunMetadata(
                input_filename=file_path.name,
                run_timestamp_utc=ts,
                output_dir=str(output_dir),
                text_model=cfg.openai_text_model,
                tts_model=cfg.openai_tts_model,
                tts_voice=voice,
                script_word_count=count_words(final_script),
                estimated_minutes=estimate_minutes(final_script),
                validation_passed=False,
                warnings=validation.warnings + validation.issues,
                token_usage={"generation": usage_gen, "repair": usage_repair},
                repaired=repaired,
                error="Validation failed; TTS skipped.",
            )
            write_json(output_dir / "metadata.json", metadata.__dict__)
            return ProcessResult(input_file=file_path, success=False, output_dir=output_dir, error=metadata.error)

        write_text(output_dir / "podcast_script.txt", final_script)
        logger.info("Final script saved. Generating audio...")

        audio_path = output_dir / "podcast_audio.mp3"
        text_to_speech(
            client=client,
            model=cfg.openai_tts_model,
            voice=voice,
            script=final_script,
            output_path=audio_path,
            retries=cfg.max_retries,
        )
        logger.info("Audio generation complete.")

        metadata = RunMetadata(
            input_filename=file_path.name,
            run_timestamp_utc=ts,
            output_dir=str(output_dir),
            text_model=cfg.openai_text_model,
            tts_model=cfg.openai_tts_model,
            tts_voice=voice,
            script_word_count=count_words(final_script),
            estimated_minutes=estimate_minutes(final_script),
            validation_passed=True,
            warnings=validation.warnings,
            token_usage={"generation": usage_gen, "repair": usage_repair},
            repaired=repaired,
        )
        write_json(output_dir / "metadata.json", metadata.__dict__)
        return ProcessResult(input_file=file_path, success=True, output_dir=output_dir)

    except Exception as exc:  # noqa: BLE001
        logger.error("File processing failed: %s", exc)
        logger.debug(traceback.format_exc())
        metadata = RunMetadata(
            input_filename=file_path.name,
            run_timestamp_utc=ts,
            output_dir=str(output_dir),
            text_model=cfg.openai_text_model,
            tts_model=cfg.openai_tts_model,
            tts_voice=voice,
            script_word_count=0,
            estimated_minutes=0.0,
            validation_passed=False,
            warnings=[],
            token_usage={},
            repaired=False,
            error=str(exc),
        )
        write_json(output_dir / "metadata.json", metadata.__dict__)
        return ProcessResult(input_file=file_path, success=False, output_dir=output_dir, error=str(exc))


def main() -> None:
    args = parse_args()
    cfg = load_config()

    ensure_dir(cfg.input_dir)
    ensure_dir(cfg.output_dir)

    voice = args.voice or cfg.openai_tts_voice
    min_words = args.min_words or cfg.min_words
    max_words = args.max_words or cfg.max_words

    app_logger = get_logger("app", level=cfg.log_level)
    files = resolve_target_files(cfg.input_dir, args.file, process_all=(args.all or args.file is None))

    if not files:
        app_logger.warning("No matching input files found in %s", cfg.input_dir)
        return

    app_logger.info("Found %d file(s) to process.", len(files))
    client = OpenAI(api_key=cfg.openai_api_key)

    results: list[ProcessResult] = []
    for file_path in files:
        result = process_file(file_path, client, cfg, voice, min_words, max_words)
        results.append(result)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    app_logger.info("Done. Success: %d | Failed: %d", success_count, fail_count)
    for result in results:
        if result.success:
            app_logger.info("OK: %s -> %s", result.input_file.name, result.output_dir)
        else:
            app_logger.error("FAIL: %s (%s)", result.input_file.name, result.error)


if __name__ == "__main__":
    main()
