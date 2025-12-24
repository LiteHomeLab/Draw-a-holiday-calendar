#!/usr/bin/env python3
"""
假日日历可视化工具
将放假通知文本转换为精美的日历图片

新版特性：两阶段流水线
1. AI 解析放假文字 → JSON 结构化数据
2. Python 渲染基础日历
3. (可选) AI 图生图美化
"""

import argparse
import configparser
import json
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

# 新版模块
from calendar_renderer import CalendarRenderer
from img2img import enhance_with_img2img, build_img2img_prompt
from parser_openai import parse_holiday_text, validate_holiday_data
from web_renderer import WebCalendarRenderer

# 保留旧版兼容性
from google import genai
from google.genai import types
from prompts import build_prompt, get_available_styles


# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.ini"


def load_config(config_path: Path = CONFIG_FILE) -> configparser.ConfigParser:
    """加载配置文件"""
    config = configparser.ConfigParser()
    if config_path.exists():
        config.read(config_path, encoding="utf-8")
    else:
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请复制 config.ini.example 为 config.ini 并填入您的 API Key"
        )
    return config


def get_api_key(config: configparser.ConfigParser) -> str:
    """从配置文件获取 API Key"""
    api_key = config.get("api", "api_key", fallback="")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError(
            "API Key 未设置。请在 config.ini 中设置 api_key"
        )
    return api_key


def generate_calendar_v2(
    holiday_text: str,
    api_key: str,
    style: str = "简约商务风",
    custom_instruction: str = "",
    aspect_ratio: str = "16:9",
    resolution: str = "2K",
    parser_base_url: str = "https://aihubmix.com/v1",
    img2img_base_url: str = "https://aihubmix.com/gemini",
    no_ai: bool = False,
    save_json: bool = False,
    save_base: bool = False,
    parser_model: str = "deepseek-v3.2",
    img2img_model: str = "gemini-2.5-flash-image",
    use_web: bool = False,
    save_html: bool = False,
    cache_dir: Path = None,
) -> bytes:
    """
    新版日历生成流程：解析 → 渲染 → (可选)图生图

    Args:
        holiday_text: 放假通知文本
        api_key: API Key
        style: 图片风格
        custom_instruction: 自定义指令
        aspect_ratio: 图片比例
        resolution: 图片分辨率
        parser_base_url: Parser API 基础 URL (OpenAI 兼容)
        img2img_base_url: 图生图 API 基础 URL (Google Genai)
        no_ai: 如果为 True，只进行基础渲染，不调用图生图
        save_json: 是否保存解析后的 JSON 数据
        save_base: 是否保存基础日历图片
        parser_model: 文本解析模型
        img2img_model: 图生图模型
        use_web: 是否使用 FullCalendar Web 渲染器
        save_html: 是否保存 HTML 文件
        cache_dir: 缓存文件存放目录，默认为脚本根目录下的 tmp 文件夹

    Returns:
        图片二进制数据 (如果是 no_ai 模式，返回基础图片的数据)
    """

    # 设置默认缓存目录
    if cache_dir is None:
        cache_dir = Path(__file__).parent / "tmp"
    # 确保缓存目录存在
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 解析放假文本为结构化 JSON
    print("=" * 50)
    print("Step 1: 解析放假通知文本...")
    print("=" * 50)

    holiday_data = parse_holiday_text(
        holiday_text=holiday_text,
        api_key=api_key,
        base_url=parser_base_url,
        model=parser_model
    )

    # 验证数据
    validate_holiday_data(holiday_data)

    print(f"解析结果:")
    print(f"  节假日: {holiday_data['holiday_name']}")
    print(f"  时间: {holiday_data['start_date']} ~ {holiday_data['end_date']}")
    print(f"  共 {holiday_data['total_days']} 天")
    if holiday_data.get('makeup_workdays'):
        print(f"  调休: {len(holiday_data['makeup_workdays'])} 天")

    # 保存 JSON 数据
    if save_json:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = cache_dir / f"holiday_data_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(holiday_data, f, ensure_ascii=False, indent=2)
        print(f"  JSON 已保存: {json_path}")

    # Step 2: 渲染基础日历
    print("\n" + "=" * 50)
    if use_web:
        print("Step 2: 使用 FullCalendar 渲染日历...")
    else:
        print("Step 2: 渲染基础日历...")
    print("=" * 50)

    if use_web:
        # 使用 Web 渲染器
        web_renderer = WebCalendarRenderer(holiday_data)

        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if save_html:
            html_path = cache_dir / f"calendar_{timestamp}.html"
        else:
            html_path = None

        # 渲染并截图
        screenshot_path = web_renderer.render(
            output_path=cache_dir / f"calendar_web_{timestamp}.png",
            width=1400,
            height=1000,
            save_html=save_html,
            html_path=html_path
        )

        # 读取截图数据
        with open(screenshot_path, "rb") as f:
            image_data = f.read()

        # --no-ai 模式：直接返回 Web 渲染结果
        if no_ai:
            print("\n--no-ai 模式: 使用 Web 渲染日历")
            return image_data

        base_image = Image.open(BytesIO(image_data))

    else:
        # 使用 Pillow 渲染器
        renderer = CalendarRenderer(holiday_data)
        base_image = renderer.render()

        # 保存基础图片
        if save_base:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_path = cache_dir / f"calendar_base_{timestamp}.png"
            base_image.save(base_path)
            print(f"  基础日历已保存: {base_path}")

        # --no-ai 模式：直接返回基础图片
        if no_ai:
            print("\n--no-ai 模式: 跳过 AI 增强，使用基础日历")
            img_buffer = BytesIO()
            base_image.save(img_buffer, format="PNG")
            return img_buffer.getvalue()

    # Step 3: 使用图生图 API 进行风格化
    print("\n" + "=" * 50)
    print("Step 3: AI 图像增强...")
    print("=" * 50)

    img2img_prompt = build_img2img_prompt(style, custom_instruction)

    enhanced_data = enhance_with_img2img(
        base_image=base_image,
        style_prompt=img2img_prompt,
        api_key=api_key,
        base_url=img2img_base_url,
        model=img2img_model,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
    )

    return enhanced_data


# ========== 保留旧版 API 以兼容性 ==========

def generate_calendar(
    holiday_text: str,
    api_key: str,
    style: str = "简约商务风",
    custom_instruction: str = "",
    aspect_ratio: str = "16:9",
    resolution: str = "2K",
    base_url: str = "https://aihubmix.com/gemini",
    model: str = "gemini-3-pro-image-preview",
) -> Optional[bytes]:
    """
    旧版 API：直接调用 Gemini 生成日历图片

    Args:
        holiday_text: 放假通知文本
        api_key: API Key
        style: 图片风格
        custom_instruction: 自定义指令
        aspect_ratio: 图片比例
        resolution: 图片分辨率
        base_url: API 基础 URL
        model: 模型名称

    Returns:
        图片二进制数据
    """
    # 构造提示词
    prompt = build_prompt(holiday_text, style, custom_instruction)

    # 初始化客户端
    client = genai.Client(
        api_key=api_key,
        http_options={"base_url": base_url},
    )

    # 调用 API 生成图片
    print(f"正在调用 {model} 生成日历图片...")
    print(f"风格: {style}")
    print(f"比例: {aspect_ratio}, 分辨率: {resolution}")

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution,
            ),
        ),
    )

    # 提取图片数据
    for part in response.parts:
        if part.text:
            print(f"AI 响应: {part.text}")
        elif inline_data := part.inline_data:
            # 直接返回图片二进制数据
            return inline_data.data

    raise RuntimeError("未能从 API 响应中获取图片数据")


def save_image(image_data: bytes, output_path: Path) -> None:
    """保存图片到文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_data)
    print(f"图片已保存: {output_path.absolute()}")


def generate_output_filename(holiday_text: str, output_dir: Path, format: str = "png") -> Path:
    """
    根据放假通知生成输出文件名

    Args:
        holiday_text: 放假通知文本
        output_dir: 输出目录
        format: 图片格式

    Returns:
        输出文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"holiday_calendar_{timestamp}.{format}"
    return output_dir / filename


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="将放假通知文本转换为精美的日历图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 新版两阶段流水线 (推荐)
  python main.py "2025年春节：1月28日至2月4日放假调休，共8天"

  # --no-ai 模式 (只生成基础日历，不调用AI增强)
  python main.py "2025年春节：1月28日至2月4日放假调休，共8天" --no-ai

  # 保存中间文件 (JSON 和基础图片)
  python main.py "放假通知..." --save-json --save-base

  # 指定输出文件
  python main.py "放假通知..." --output my_calendar.png

  # 使用不同风格
  python main.py "放假通知..." --style "中国红喜庆风"

  # 使用自定义指令
  python main.py "放假通知..." --custom "使用蓝色主题，添加公司Logo"

  # 列出所有可用风格
  python main.py --list-styles
        """
    )

    parser.add_argument(
        "holiday_text",
        nargs="?",
        help="放假通知文本",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="输出图片文件路径 (默认: holiday_calendar_时间戳.png)",
    )

    parser.add_argument(
        "-s", "--style",
        default="简约商务风",
        choices=get_available_styles(),
        help="图片风格预设",
    )

    parser.add_argument(
        "-c", "--custom",
        default="",
        help="自定义绘图指令（覆盖风格预设）",
    )

    parser.add_argument(
        "--aspect-ratio",
        default="16:9",
        choices=["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        help="图片比例 (默认: 16:9)",
    )

    parser.add_argument(
        "--resolution",
        default="2K",
        choices=["1K", "2K", "4K"],
        help="图片分辨率 (默认: 2K)",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_FILE,
        help=f"配置文件路径 (默认: {CONFIG_FILE})",
    )

    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="列出所有可用的风格预设",
    )

    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpg"],
        help="输出图片格式 (默认: png)",
    )

    # 新增参数
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="只生成基础日历，不调用图生图 API 进行增强",
    )

    parser.add_argument(
        "--save-json",
        action="store_true",
        help="保存解析后的 JSON 数据",
    )

    parser.add_argument(
        "--save-base",
        action="store_true",
        help="保存基础渲染的日历图片",
    )

    # Web 渲染器参数
    parser.add_argument(
        "--web",
        action="store_true",
        help="使用 FullCalendar Web 渲染器（需要安装 playwright）",
    )

    parser.add_argument(
        "--save-html",
        action="store_true",
        help="保存生成的 HTML 文件",
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="缓存文件存放目录 (默认: 脚本根目录下的 tmp 文件夹)",
    )

    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_arguments()

    # 列出风格
    if args.list_styles:
        print("可用的风格预设:")
        for style in get_available_styles():
            print(f"  - {style}")
        return 0

    # 检查必需参数
    if not args.holiday_text:
        print("错误: 请提供放假通知文本", file=sys.stderr)
        print("使用 python main.py --help 查看帮助", file=sys.stderr)
        return 1

    try:
        # 加载配置
        config = load_config(args.config)
        api_key = get_api_key(config)

        # Parser API 配置 (OpenAI 兼容)
        parser_base_url = config.get("parser", "base_url",
                                      fallback="https://aihubmix.com/v1")
        parser_model = config.get("parser", "model",
                                  fallback="deepseek-v3.2")

        # Img2Img API 配置 (Google Genai)
        img2img_base_url = config.get("generation", "base_url",
                                       fallback="https://aihubmix.com/gemini")
        img2img_model = config.get("generation", "model",
                                   fallback="gemini-2.5-flash-image")

        # 输出配置
        output_dir_str = config.get("output", "output_dir", fallback="")

        # 生成图片 (新版两阶段流水线)
        image_data = generate_calendar_v2(
            holiday_text=args.holiday_text,
            api_key=api_key,
            style=args.style,
            custom_instruction=args.custom,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            parser_base_url=parser_base_url,
            img2img_base_url=img2img_base_url,
            no_ai=args.no_ai,
            save_json=args.save_json,
            save_base=args.save_base,
            parser_model=parser_model,
            img2img_model=img2img_model,
            use_web=args.web,
            save_html=args.save_html,
            cache_dir=args.cache_dir,
        )

        # 确定输出路径
        if args.output:
            output_path = args.output
        else:
            output_dir = Path(output_dir_str) if output_dir_str else Path.cwd()
            output_path = generate_output_filename(args.holiday_text, output_dir, args.format)

        # 保存图片
        save_image(image_data, output_path)

        return 0

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
