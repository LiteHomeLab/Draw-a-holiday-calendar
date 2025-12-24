# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication & Development Rules

1. **使用中文回答问题** - Use Chinese to respond to user questions and explanations
2. **开发环境** - Primary development platform is **Windows** (`platform: win32`)
3. **BAT 脚本规范** - BAT script files must NOT contain Chinese characters; use English only for comments and output
4. **脚本修复原则** - When asked to fix a script, edit the existing file in-place. Only create a new script when absolutely necessary

## Project Overview

Draw-a-holiday-calendar is a Python CLI tool that converts holiday notice text into beautifully designed calendar images using a **two-stage pipeline architecture**:

1. **Parse**: AI extracts structured holiday data (dates, duration, makeup workdays) from text
2. **Render**: FullCalendar generates beautiful calendar images

This architecture separates data extraction from visual generation, ensuring date accuracy.

## Common Commands

```bash
# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install

# Generate calendar
uv run python main.py "2025年春节：1月28日至2月4日放假调休，共8天"

# Save JSON data
uv run python main.py "放假通知..." --save-json

# Save HTML file
uv run python main.py "放假通知..." --save-html

# Specify output file
uv run python main.py "放假通知..." --output my_calendar.png
```

## Architecture

### Core Pipeline

```
holiday_text → parser_openai.py → JSON → web_renderer.py → calendar.png
```

### Module Responsibilities

| Module | Purpose | API Used |
|--------|---------|----------|
| `parser_openai.py` | Parse holiday text → structured JSON | OpenAI-compatible (deepseek-v3.2) |
| `web_renderer.py` | Render calendar using FullCalendar | Playwright (screenshot) |
| `main.py` | CLI entry point and pipeline orchestration | - |

### JSON Data Schema

The parser produces this structure (validated before rendering):

```json
{
  "holiday_name": "2025年春节",
  "year": 2025,
  "month": 1,
  "start_date": "2025-01-28",
  "end_date": "2025-02-04",
  "total_days": 8,
  "holiday_dates": ["2025-01-28", "2025-01-29", ...],
  "makeup_workdays": [{"date": "2025-01-26", "description": "周日上班"}],
  "calendar_months": [1, 2],
  "notes": "春节期间高速免费"
}
```

## Configuration

`config.ini` contains three sections:

```ini
[api]
api_key = sk-...           # AIHubMix API key

[parser]
base_url = https://aihubmix.com/v1
model = deepseek-v3.2      # Text parsing model

[output]
output_dir =
format = png
```

## Key Implementation Notes

### CLI Flags

- `--save-json`: Save parsed JSON data (useful for debugging parser)
- `--save-html`: Save generated HTML file
- `--cache-dir`: Specify cache directory
- `-o, --output`: Specify output file path
- `--format`: Output format (png/jpg)

### Error Handling

- JSON schema validation before rendering
- Date format verification (YYYY-MM-DD)
- API failures preserve intermediate outputs when using `--save-json`

## Development

When adding features:

1. **New output formats**: Update `[output]` config section
2. **New models**: Update `model` defaults in respective config sections
3. **Web renderer styling**: Modify `templates/calendar_template.html`
