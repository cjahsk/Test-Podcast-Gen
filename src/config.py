from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_text_model: str = Field("gpt-4.1-mini", alias="OPENAI_TEXT_MODEL")
    openai_tts_model: str = Field("gpt-4o-mini-tts", alias="OPENAI_TTS_MODEL")
    openai_tts_voice: str = Field("alloy", alias="OPENAI_TTS_VOICE")

    input_dir: Path = Field(Path("inputs"), alias="INPUT_DIR")
    output_dir: Path = Field(Path("outputs"), alias="OUTPUT_DIR")

    min_words: int = Field(120, alias="MIN_WORDS")
    max_words: int = Field(350, alias="MAX_WORDS")
    allow_missing_sections: bool = Field(False, alias="ALLOW_MISSING_SECTIONS")
    allow_bullets: bool = Field(False, alias="ALLOW_BULLETS")
    enable_repair_pass: bool = Field(True, alias="ENABLE_REPAIR_PASS")
    max_retries: int = Field(2, alias="MAX_RETRIES")
    log_level: str = Field("INFO", alias="LOG_LEVEL")



def load_config() -> AppConfig:
    load_dotenv(override=False)
    return AppConfig()
