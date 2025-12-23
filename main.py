#!/usr/bin/env python3
"""
假日日历可视化工具
将放假通知文本转换为精美的日历图片
"""

import argparse
import configparser
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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
    调用 Gemini 3 Pro Image Preview 生成日历图片

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
    # 尝试从文本中提取年份和月份
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
  # 基础用法
  python main.py "2024年春节放假安排：2月9日至17日放假，共9天"

  # 指定输出文件
  python main.py "放假通知..." --output my_calendar.png

  # 使用不同风格
  python main.py "放假通知..." --style "现代多彩风"

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

        # 获取配置
        model = config.get("generation", "model", fallback="gemini-3-pro-image-preview")
        base_url = config.get("generation", "base_url", fallback="https://aihubmix.com/gemini")
        output_dir_str = config.get("output", "output_dir", fallback="")

        # 生成图片
        image_data = generate_calendar(
            holiday_text=args.holiday_text,
            api_key=api_key,
            style=args.style,
            custom_instruction=args.custom,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            base_url=base_url,
            model=model,
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
