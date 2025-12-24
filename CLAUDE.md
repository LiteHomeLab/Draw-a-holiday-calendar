# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication & Development Rules

1. **使用中文回答问题** - Use Chinese to respond to user questions and explanations
2. **开发环境** - Primary development platform is **Windows** (`platform: win32`)
3. **BAT 脚本规范** - BAT script files must NOT contain Chinese characters; use English only for comments and output
4. **脚本修复原则** - When asked to fix a script, edit the existing file in-place. Only create a new script when absolutely necessary

## Project Overview

Draw-a-holiday-calendar is a Python CLI tool that converts holiday notice text into beautifully designed calendar images using a **three-stage pipeline architecture**:

1. **Parse**: AI extracts structured holiday data (dates, duration, makeup workdays) from text
2. **Render**: Python + Pillow generates a clean, structured base calendar
3. **Enhance** (optional): AI image-to-image improves visual styling

This architecture separates data extraction from visual generation, ensuring date accuracy while enabling creative styling.

## Common Commands

```bash
# Install dependencies
uv sync

# Run full pipeline (parse → render → AI enhance)
uv run python main.py "2025年春节：1月28日至2月4日放假调休，共8天"

# Base calendar only (no AI enhancement - pure Python)
uv run python main.py "放假通知..." --no-ai

# Save intermediate files for debugging
uv run python main.py "放假通知..." --save-json --save-base

# List available style presets
uv run python main.py --list-styles

# Custom styling
uv run python main.py "放假通知..." --style "中国红喜庆风" --aspect-ratio 16:9 --resolution 2K
```

## Architecture

### Core Pipeline

```
holiday_text → parser_openai.py → JSON → calendar_renderer.py → base.png → img2img.py → final.png
```

### Module Responsibilities

| Module | Purpose | API Used |
|--------|---------|----------|
| `parser_openai.py` | Parse holiday text → structured JSON | OpenAI-compatible (deepseek-v3.2) |
| `calendar_renderer.py` | Render base calendar from JSON | Pure Python (Pillow + calendar) |
| `img2img.py` | Style enhancement via image-to-image | Google GenAI (gemini-2.5-flash-image) |
| `main.py` | CLI entry point and pipeline orchestration | - |
| `prompts/templates.py` | Style presets and prompt templates | - |

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

### Cross-Platform Font Handling

`CalendarRenderer._get_font()` implements platform-specific font detection:

- **Windows**: 微软雅黑 → 黑体 → 宋体
- **Linux**: WenQuanYi Microhei → Noto Sans CJK
- **macOS**: PingFang SC → STHeiti
- Fallback to default if none found

## Configuration

`config.ini` contains three sections:

```ini
[api]
api_key = sk-...           # AIHubMix API key

[parser]
base_url = https://aihubmix.com/v1
model = deepseek-v3.2      # Text parsing model

[generation]
base_url = https://aihubmix.com/gemini
model = gemini-3-pro-image-preview  # Image enhancement model
aspect_ratio = 16:9
resolution = 2K

[output]
output_dir =
format = png
```

## Style Presets

Defined in `prompts/templates.py`:

| Style | Description |
|-------|-------------|
| 简约商务风 | Minimalist black/white/gray, corporate |
| 现代多彩风 | Vibrant gradients, social media friendly |
| 中国红喜庆风 | Traditional red/gold with lanterns/clouds |
| 扁平化设计 | Flat UI, solid colors, geometric |

## Key Implementation Notes

### CLI Flags

- `--no-ai`: Skip AI enhancement, output base calendar only
- `--save-json`: Save parsed JSON data (useful for debugging parser)
- `--save-base`: Save base rendered image (before AI enhancement)

### Cost Optimization Strategy

- Parser uses cheaper text models (deepseek-v3.2) for JSON extraction
- Enhancement only uses expensive image models when needed
- `--no-ai` mode enables pure Python operation with zero API costs

### Error Handling

- JSON schema validation before rendering
- Date format verification (YYYY-MM-DD)
- Graceful fallback for missing fonts
- API failures preserve intermediate outputs when using `--save-base`

## Development

When adding features:

1. **New style presets**: Add to `STYLE_PRESETS` in `prompts/templates.py`
2. **New output formats**: Modify `calendar_renderer.py` and update `[output]` config section
3. **New models**: Update `model` defaults in respective config sections
