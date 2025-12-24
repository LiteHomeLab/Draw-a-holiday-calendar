#!/usr/bin/env python3
"""
假日日历可视化工具
将放假通知文本转换为精美的日历图片

特性：
1. AI 解析放假文字 → JSON 结构化数据
2. Web 渲染日历（FullCalendar）
"""

import argparse
import configparser
import json
import sys
from datetime import datetime
from pathlib import Path

# 模块导入
from parser_openai import parse_holiday_text, validate_holiday_data
from web_renderer import WebCalendarRenderer


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
    parser_base_url: str = "https://aihubmix.com/v1",
    save_json: bool = False,
    save_html: bool = False,
    parser_model: str = "deepseek-v3.2",
    cache_dir: Path = None,
) -> bytes:
    """
    日历生成流程：解析 → 渲染

    Args:
        holiday_text: 放假通知文本
        api_key: API Key
        parser_base_url: Parser API 基础 URL (OpenAI 兼容)
        save_json: 是否保存解析后的 JSON 数据
        save_html: 是否保存 HTML 文件
        parser_model: 文本解析模型
        cache_dir: 缓存文件存放目录，默认为脚本根目录下的 tmp 文件夹

    Returns:
        图片二进制数据
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

    # Step 2: 渲染日历
    print("\n" + "=" * 50)
    print("Step 2: 使用 FullCalendar 渲染日历...")
    print("=" * 50)

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

    return image_data


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
  # 生成日历
  python main.py "2025年春节：1月28日至2月4日放假调休，共8天"

  # 保存 JSON 数据
  python main.py "放假通知..." --save-json

  # 指定输出文件
  python main.py "放假通知..." --output my_calendar.png

  # 保存 HTML 文件
  python main.py "放假通知..." --save-html

  # 从 JSON 文件渲染（快速调试，无需 API 调用）
  python main.py --load-json tmp/holiday_data_20251224_154630.json

  # 从 JSON 文件渲染并保存 HTML
  python main.py --load-json tmp/holiday_data_20251224_154630.json --save-html -o output.png
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
        "--config",
        type=Path,
        default=CONFIG_FILE,
        help=f"配置文件路径 (默认: {CONFIG_FILE})",
    )

    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpg"],
        help="输出图片格式 (默认: png)",
    )

    parser.add_argument(
        "--save-json",
        action="store_true",
        help="保存解析后的 JSON 数据",
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

    parser.add_argument(
        "--load-json",
        type=Path,
        dest="load_json",
        help="从 JSON 文件加载数据（跳过 API 解析，用于快速调试渲染）",
    )

    return parser.parse_args()


def render_from_json(
    json_path: Path,
    save_html: bool = False,
    cache_dir: Path = None,
) -> bytes:
    """
    从 JSON 文件直接渲染日历（跳过 API 解析）

    Args:
        json_path: JSON 文件路径
        save_html: 是否保存 HTML 文件
        cache_dir: 缓存文件存放目录

    Returns:
        图片二进制数据
    """
    # 设置默认缓存目录
    if cache_dir is None:
        cache_dir = Path(__file__).parent / "tmp"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 读取 JSON 数据
    print(f"从 JSON 文件加载数据: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        holiday_data = json.load(f)

    # 验证数据
    validate_holiday_data(holiday_data)

    print(f"假期: {holiday_data['holiday_name']}")
    print(f"时间: {holiday_data['start_date']} ~ {holiday_data['end_date']}")
    print(f"共 {holiday_data['total_days']} 天")

    # 渲染日历
    print("\n渲染日历...")
    web_renderer = WebCalendarRenderer(holiday_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if save_html:
        html_path = cache_dir / f"calendar_{timestamp}.html"
    else:
        html_path = None

    # 渲染并截图
    screenshot_path = web_renderer.render(
        output_path=cache_dir / f"calendar_web_{timestamp}.png",
        width=None,  # 自动计算宽度
        height=1000,
        save_html=save_html,
        html_path=html_path
    )

    with open(screenshot_path, "rb") as f:
        return f.read()


def main() -> int:
    """主函数"""
    args = parse_arguments()

    try:
        # 设置缓存目录
        cache_dir = args.cache_dir or (Path(__file__).parent / "tmp")
        cache_dir.mkdir(parents=True, exist_ok=True)

        # 模式1: 从 JSON 文件加载（调试模式）
        if args.load_json:
            if not args.load_json.exists():
                print(f"错误: JSON 文件不存在: {args.load_json}", file=sys.stderr)
                return 1

            image_data = render_from_json(
                json_path=args.load_json,
                save_html=args.save_html,
                cache_dir=cache_dir,
            )

            # 确定输出路径
            if args.output:
                output_path = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = cache_dir / f"calendar_{timestamp}.png"

            save_image(image_data, output_path)
            return 0

        # 模式2: 正常流程（文本 → API解析 → 渲染）
        # 检查必需参数
        if not args.holiday_text:
            print("错误: 请提供放假通知文本，或使用 --load-json 从 JSON 文件加载", file=sys.stderr)
            print("使用 python main.py --help 查看帮助", file=sys.stderr)
            return 1

        # 加载配置
        config = load_config(args.config)
        api_key = get_api_key(config)

        # Parser API 配置 (OpenAI 兼容)
        parser_base_url = config.get("parser", "base_url",
                                      fallback="https://aihubmix.com/v1")
        parser_model = config.get("parser", "model",
                                  fallback="deepseek-v3.2")

        # 输出配置
        output_dir_str = config.get("output", "output_dir", fallback="")

        # 生成图片
        image_data = generate_calendar_v2(
            holiday_text=args.holiday_text,
            api_key=api_key,
            parser_base_url=parser_base_url,
            save_json=args.save_json,
            save_html=args.save_html,
            parser_model=parser_model,
            cache_dir=cache_dir,
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
