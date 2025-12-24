# 假日日历可视化工具

将放假通知文本转换为精美的日历图片的命令行工具。

## 新版特性

**两阶段流水线架构**，实现更可控的输出：

1. **解析阶段**：AI 解析放假文字 → JSON 结构化数据
2. **渲染阶段**：Python 使用 JSON 绘制基础日历
3. **增强阶段**（可选）：AI 图生图美化

### 新版优势

| 特性 | 旧版 | 新版 |
|------|------|------|
| 日期准确性 | 依赖 AI 理解 | 结构化数据保证 |
| 输出可控性 | 低 | 高（可查看中间结果） |
| 调试能力 | 难以调试 | 可保存 JSON 和基础图 |
| 成本 | 单次高成本模型 | 解析用低成本模型 |
| 纯本地模式 | 不支持 | `--no-ai` 支持 |

## 功能特点

- 支持多种预设风格（简约商务风、现代多彩风、中国红喜庆风、扁平化设计）
- 支持自定义绘图指令
- 支持多种图片比例和分辨率
- **新增**：`--no-ai` 模式，仅生成基础日历
- **新增**：`--save-json` 保存解析后的结构化数据
- **新增**：`--save-base` 保存基础渲染图片
- 通过配置文件管理 API Key
- 命令行接口，便于脚本调用

## 环境要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Python 包管理工具

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

3. 配置 API Key

编辑 `config.ini` 文件，填入你的 AIHubMix API Key：

```ini
[api]
api_key = YOUR_API_KEY_HERE
```

获取 API Key: https://aihubmix.com

## 使用方法

### 新版推荐用法

```bash
# 完整流水线 (解析 → 渲染 → AI 增强)
uv run python main.py "2025年春节：1月28日至2月4日放假调休，共8天"

# --no-ai 模式 (只生成基础日历，不调用 AI 增强)
uv run python main.py "2025年春节：1月28日至2月4日放假调休，共8天" --no-ai

# 保存中间文件 (JSON 数据和基础图片)
uv run python main.py "放假通知..." --save-json --save-base
```

### 基础用法

```bash
uv run python main.py "2024年春节放假安排：2月9日至17日放假，共9天"
```

### 指定输出文件

```bash
uv run python main.py "放假通知..." --output my_calendar.png
```

### 使用不同风格

```bash
# 现代多彩风
uv run python main.py "放假通知..." --style "现代多彩风"

# 中国红喜庆风
uv run python main.py "放假通知..." --style "中国红喜庆风"
```

### 使用自定义指令

```bash
uv run python main.py "放假通知..." --custom "使用蓝色主题，添加公司Logo"
```

### 调整图片比例和分辨率

```bash
# 正方形，4K 分辨率
uv run python main.py "放假通知..." --aspect-ratio 1:1 --resolution 4K

# 竖屏，2K 分辨率
uv run python main.py "放假通知..." --aspect-ratio 9:16 --resolution 2K
```

### 列出所有可用风格

```bash
uv run python main.py --list-styles
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `holiday_text` | 放假通知文本 | 必需 |
| `-o, --output` | 输出图片文件路径 | `holiday_calendar_时间戳.png` |
| `-s, --style` | 图片风格预设 | 简约商务风 |
| `-c, --custom` | 自定义绘图指令 | 空 |
| `--aspect-ratio` | 图片比例 | 16:9 |
| `--resolution` | 图片分辨率 (1K/2K/4K) | 2K |
| `--format` | 输出格式 (png/jpg) | png |
| `--config` | 配置文件路径 | config.ini |
| `--list-styles` | 列出所有可用风格 | - |
| `--no-ai` | 只生成基础日历，不调用 AI 增强 | False |
| `--save-json` | 保存解析后的 JSON 数据 | False |
| `--save-base` | 保存基础渲染图片 | False |

## 配置文件

`config.ini` 文件结构：

```ini
[api]
# AIHubMix API Key
api_key = YOUR_API_KEY_HERE

[parser]
# 文本解析模型（用于解析放假通知文本）
model = gemini-2.0-flash-exp

[generation]
# 图生图模型（用于美化基础日历）
model = gemini-2.5-flash-image

# 图片比例: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
aspect_ratio = 16:9

# 图片分辨率: 1K, 2K, 4K
resolution = 2K

# API 基础 URL
base_url = https://aihubmix.com/gemini

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

## 风格预设

| 风格 | 描述 |
|------|------|
| 简约商务风 | 简约黑白灰配色，适合正式场合 |
| 现代多彩风 | 渐变色彩，现代图标设计 |
| 中国红喜庆风 | 传统红金配色，灯笼祥云装饰 |
| 扁平化设计 | 扁平 UI 风格，纯色块设计 |

## 项目结构

```
draw-a-holiday-calendar/
├── main.py                 # 入口脚本
├── parser.py               # 放假文本解析模块 (新增)
├── calendar_renderer.py    # 日历渲染模块 (新增)
├── img2img.py              # 图生图增强模块 (新增)
├── config.ini              # 配置文件
├── pyproject.toml          # 项目配置
├── prompts/
│   ├── __init__.py
│   └── templates.py        # 提示词模板
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
│  │ (文本)       │     │ (gemini-2.0) │      │              │   │
│  └──────────────┘     └──────────────┘      └──────────────┘   │
│                                                                 │
│  Step 2: 渲染基础日历                                           │
│  ┌──────────────┐     ┌──────────────┐      ┌──────────────┐   │
│  │ JSON 数据    │ ──▶ │ 日历渲染器   │ ──▶  │ 基础图片    │   │
│  │              │     │ (Python+PIL) │      │ (PNG/PIL)    │   │
│  └──────────────┘     └──────────────┘      └──────────────┘   │
│                                                                 │
│  Step 3: AI 图像增强 (可选，跳过 if --no-ai)                    │
│  ┌──────────────┐     ┌──────────────┐      ┌──────────────┐   │
│  │ 基础图片     │ ──▶ │ 图生图 AI    │ ──▶  │ 最终图片    │   │
│  │ + 风格提示   │     │ (gemini-2.5) │      │ (美化后)     │   │
│  └──────────────┘     └──────────────┘      └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 许可证

MIT License
