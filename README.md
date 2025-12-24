# 假日日历可视化工具

将放假通知文本转换为精美的日历图片的命令行工具。

## 特性

**流水线架构**，实现更可控的输出：

1. **解析阶段**：AI 解析放假文字 → JSON 结构化数据
2. **渲染阶段**：使用 FullCalendar 渲染精美的日历图片

### 新版优势

| 特性 | 旧版 | 新版 |
|------|------|------|
| 日期准确性 | 依赖 AI 理解 | 结构化数据保证 |
| 输出可控性 | 低 | 高（可查看中间结果） |
| 调试能力 | 难以调试 | 可保存 JSON 数据 |
| 成本 | 单次高成本模型 | 解析用低成本模型 |

## 功能特点

- 结构化数据保证日期准确性
- 使用 FullCalendar 渲染美观的现代样式日历
- `--save-json` 保存解析后的结构化数据
- `--save-html` 保存生成的 HTML 文件
- 通过配置文件管理 API Key
- 命令行接口，便于脚本调用

## 环境要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Python 包管理工具
- playwright (用于浏览器截图)

## 安装

1. 克隆仓库
```bash
git clone https://github.com/LiteHomeLab/Draw-a-holiday-calendar.git
cd Draw-a-holiday-calendar
```

2. 安装依赖
```bash
uv sync
```

3. 安装 Playwright 浏览器
```bash
uv run playwright install
```

4. 配置 API Key

编辑 `config.ini` 文件，填入你的 AIHubMix API Key：

```ini
[api]
api_key = YOUR_API_KEY_HERE
```

获取 API Key: https://aihubmix.com

## 使用方法

```bash
# 生成日历
uv run python main.py "2025年春节：1月28日至2月4日放假调休，共8天"

# 保存 JSON 数据
uv run python main.py "放假通知..." --save-json

# 保存 HTML 文件
uv run python main.py "放假通知..." --save-html

# 指定缓存目录
uv run python main.py "放假通知..." --save-json --cache-dir "./my_cache"

# 指定输出文件
uv run python main.py "放假通知..." --output my_calendar.png
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `holiday_text` | 放假通知文本 | 必需 |
| `-o, --output` | 输出图片文件路径 | `holiday_calendar_时间戳.png` |
| `--format` | 输出格式 (png/jpg) | png |
| `--config` | 配置文件路径 | config.ini |
| `--save-json` | 保存解析后的 JSON 数据 | False |
| `--save-html` | 保存生成的 HTML 文件 | False |
| `--cache-dir` | 缓存文件存放目录 | `tmp/` |

## 配置文件

`config.ini` 文件结构：

```ini
[api]
# AIHubMix API Key
api_key = YOUR_API_KEY_HERE

[parser]
# 文本解析模型（用于解析放假通知文本）
base_url = https://aihubmix.com/v1
model = deepseek-v3.2

[output]
# 默认输出目录 (留空表示当前目录)
output_dir =

# 默认图片格式: png, jpg
format = png
```

## JSON 数据结构

解析后的假期数据格式：

```json
{
  "holiday_name": "2025年春节",
  "year": 2025,
  "month": 1,
  "start_date": "2025-01-28",
  "end_date": "2025-02-04",
  "total_days": 8,
  "holiday_dates": [
    "2025-01-28",
    "2025-01-29",
    "2025-01-30",
    "2025-01-31",
    "2025-02-01",
    "2025-02-02",
    "2025-02-03",
    "2025-02-04"
  ],
  "makeup_workdays": [
    {
      "date": "2025-01-26",
      "description": "周日上班"
    },
    {
      "date": "2025-02-08",
      "description": "周六上班"
    }
  ],
  "calendar_months": [1, 2],
  "notes": "春节期间高速免费"
}
```

## 项目结构

```
draw-a-holiday-calendar/
├── main.py                 # 入口脚本
├── parser_openai.py        # 放假文本解析模块 (OpenAI 兼容 API)
├── web_renderer.py         # Web 日历渲染模块 (FullCalendar)
├── config.ini              # 配置文件
├── pyproject.toml          # 项目配置
├── prompts/
│   ├── __init__.py
│   └── templates.py        # 提示词模板
├── templates/
│   └── calendar_template.html  # FullCalendar HTML 模板
├── tmp/                    # 缓存目录 (自动生成，已加入 .gitignore)
└── README.md
```

## 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    假日日历生成流水线                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 解析放假文字                                           │
│  ┌──────────────┐     ┌──────────────┐      ┌──────────────┐   │
│  │ 用户输入     │ ──▶ │ AI 解析器    │ ──▶  │ JSON 数据    │   │
│  │ (文本)       │     │ (deepseek)   │      │              │   │
│  └──────────────┘     └──────────────┘      └──────────────┘   │
│                                                                 │
│  Step 2: 渲染日历                                               │
│  ┌──────────────┐     ┌──────────────┐      ┌──────────────┐   │
│  │ JSON 数据    │ ──▶ │ Web 渲染器   │ ──▶  │ 最终图片    │   │
│  │              │     │ (FullCalendar│      │ (PNG)        │   │
│  └──────────────┘     └──────────────┘      └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 许可证

MIT License
