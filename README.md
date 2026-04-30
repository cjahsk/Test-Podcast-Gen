# Local Podcast Generator (Python)

A lightweight local-first Python tool that turns product information documents into:

1. A podcast-ready script (plain text)
2. An MP3 audio file using OpenAI text-to-speech

It is designed for short internal training/briefing content for field sales teams.

---

## What this project does

The app can run in two modes:

1. **Single-file mode** (`--file <name>`): one input -> one script + one MP3
2. **Combined mode** (default when multiple files are found): all inputs -> one joined script + one joined MP3

For both modes, the app:

1. Reads and extracts text from local documents (`.txt`, `.md`, `.pdf`, `.docx`, `.csv`)
2. Cleans the extracted text
3. Uses an OpenAI text model to draft a podcast script
4. Validates the draft against simple business rules
5. Optionally runs one repair pass if validation fails
6. Converts validated script to MP3 with OpenAI TTS
7. Saves script/audio/log/metadata in a dedicated output folder

No web UI, no database, no cloud hosting setup.

---

## Requirements

- Windows PC (or any OS with Python)
- Python **3.11+**
- OpenAI API key
- Internet connection for OpenAI API calls

---

## Project structure

```text
project/
  inputs/
  outputs/
  prompts/
    script_system_prompt.txt
    script_repair_prompt.txt
  src/
    __init__.py
    clean.py
    config.py
    extract.py
    generate_script.py
    ingest.py
    main.py
    models.py
    tts.py
    utils.py
    validate.py
  .env.example
  requirements.txt
  README.md
```

---

## Setup (Windows PowerShell)

### 1) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Create your `.env`

```powershell
copy .env.example .env
```

Then open `.env` and set at least:

- `OPENAI_API_KEY`

You can keep default values for the rest initially.

---

## Add input files

Put your files in the `inputs/` folder. Supported formats:

- `.txt`
- `.md`
- `.pdf`
- `.docx`
- `.csv`

---

## Run the app

### Process all supported files (default: creates one combined podcast)

```powershell
python -m src.main
```

### Process one file only

```powershell
python -m src.main --file my_product_sheet.pdf
```

### Explicit all flag

```powershell
python -m src.main --all
```

### Override voice and word-count range

```powershell
python -m src.main --voice alloy --min-words 140 --max-words 320
```

---

## Outputs

Outputs are saved under:

```text
outputs/<timestamp>_<input-slug>/
```

or (for combined mode):

```text
outputs/<timestamp>_batch_podcast/
```

Example files:

- `source_text.txt` (cleaned extracted source, or combined source in batch mode)
- `podcast_script_draft.txt` (first model draft)
- `podcast_script_repaired.txt` (only if repair was needed)
- `podcast_script.txt` (final approved script)
- `podcast_audio.mp3` (generated speech)
- `metadata.json` (run details)
- `source_manifest.json` (batch mode: included/skipped input files)
- `run.log` (run logs)

---

## Configuration reference (`.env`)

- `OPENAI_API_KEY` – required
- `OPENAI_TEXT_MODEL` – script generation model (default `gpt-4.1-mini`)
- `OPENAI_TTS_MODEL` – TTS model (default `gpt-4o-mini-tts`)
- `OPENAI_TTS_VOICE` – voice name (default `alloy`)
- `INPUT_DIR` – input folder (default `inputs`)
- `OUTPUT_DIR` – output folder (default `outputs`)
- `MIN_WORDS` – minimum script words (default `120`)
- `MAX_WORDS` – maximum script words (default `350`)
- `ALLOW_MISSING_SECTIONS` – allow looser section coverage (`true`/`false`)
- `ALLOW_BULLETS` – allow bullet points (`true`/`false`)
- `ENABLE_REPAIR_PASS` – one repair pass on validation failure (`true`/`false`)
- `MAX_RETRIES` – retry count for transient API failures
- `LOG_LEVEL` – `DEBUG`, `INFO`, `WARNING`, etc.

---

## Validation checks

The script validator checks for:

- Minimum and maximum word count
- Markdown headings (`#`, `##`) not allowed
- Bullet points / numbered lists not allowed (unless configured)
- Placeholder text (e.g., `insert ... here`, bracket placeholders)
- Basic section coverage (unless configured to allow missing sections)
- Suspicious superlative phrasing (warning)
- Uncommon characters that may affect TTS (warning)

If validation still fails after optional repair, TTS is skipped and error details are logged.

---

## Common errors and fixes

### `OPENAI_API_KEY` missing
- Ensure `.env` exists and includes `OPENAI_API_KEY=...`

### No files processed
- Confirm files are in `inputs/`
- Check file extensions are supported

### PDF extraction is weak
- Some PDFs are scanned images and contain little selectable text
- Use a text-based PDF or pre-convert with OCR before processing

### TTS/API failures
- Check internet connection
- Confirm model and voice names in `.env`
- Retry later if API rate limits occur

### Script fails validation repeatedly
- Lower `MIN_WORDS` or increase `MAX_WORDS`
- Set `ALLOW_MISSING_SECTIONS=true` for very thin source material

---

## Assumptions

- Input documents are in English or mostly English.
- PDFs are text-extractable (not image-only scans).
- OpenAI models and voice names used in defaults are available to your account.

