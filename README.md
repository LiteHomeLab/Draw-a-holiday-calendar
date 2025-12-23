# 假日日历可视化工具

将放假通知文本转换为精美的日历图片的命令行工具。

## 功能特点

- 支持多种预设风格（简约商务风、现代多彩风、中国红喜庆风、扁平化设计）
- 支持自定义绘图指令
- 支持多种图片比例和分辨率
- 使用 Gemini 3 Pro Image Preview 生成高质量图片
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

## 配置文件

`config.ini` 文件结构：

```ini
[api]
# AIHubMix API Key
api_key = YOUR_API_KEY_HERE

[generation]
# 图片默认配置
model = gemini-3-pro-image-preview

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
├── main.py              # 入口脚本
├── config.ini           # 配置文件
├── pyproject.toml       # 项目配置
├── prompts/
│   ├── __init__.py
│   └── templates.py     # 提示词模板
└── README.md
```

## 许可证

MIT License
