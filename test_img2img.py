#!/usr/bin/env python3
"""
测试图生图精绘提示词

使用 tmp 文件夹下的测试图片进行测试
"""

import configparser
from pathlib import Path
from PIL import Image

# 导入配置和函数
from img2img import (
    build_img2img_prompt,
    enhance_with_img2img,
    save_image,
)


def test_prompt_generation():
    """测试提示词生成"""
    print("=" * 60)
    print("测试精绘提示词生成")
    print("=" * 60)

    # 生成提示词
    prompt = build_img2img_prompt()
    print(f"\n提示词长度: {len(prompt)} 字符")
    print(f"\n提示词预览:\n{prompt[:800]}...")
    print()


def test_img2img_enhancement():
    """测试图生图增强功能"""
    print("\n" + "=" * 60)
    print("测试图生图增强")
    print("=" * 60)

    # 查找测试图片
    tmp_dir = Path("tmp")
    test_images = list(tmp_dir.glob("calendar_*.png")) + list(tmp_dir.glob("calendar_*.jpg"))

    if not test_images:
        print(f"错误: 未找到测试图片")
        print("请确保 tmp 文件夹下有 calendar_*.png 或 calendar_*.jpg 文件")
        return

    # 使用最新的图片
    test_image_path = sorted(test_images)[-1]
    print(f"加载测试图片: {test_image_path}")
    base_image = Image.open(test_image_path)
    print(f"图片尺寸: {base_image.size}")

    # 加载配置
    config = configparser.ConfigParser()
    config_path = Path("config.ini")
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        return

    config.read(config_path, encoding="utf-8")

    api_key = config.get("api", "api_key", fallback=None)
    base_url = config.get("generation", "base_url", fallback="https://aihubmix.com/v1")
    model = config.get("generation", "model", fallback="gemini-2.5-flash-image")

    if not api_key:
        print("错误: 未配置 API Key")
        return

    print(f"\nAPI 端点: {base_url}")
    print(f"模型: {model}")

    # 构建提示词
    prompt = build_img2img_prompt()
    print(f"\n提示词已构建 (长度: {len(prompt)} 字符)")

    try:
        # 调用图生图 API
        print(f"\n正在调用 {model} 进行增强...")
        enhanced_data = enhance_with_img2img(
            base_image=base_image,
            style_prompt=prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

        # 保存结果
        output_dir = Path("tmp/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"enhanced_{test_image_path.stem}.png"
        save_image(enhanced_data, output_path)
        print(f"\n[SUCCESS] 增强成功! 结果已保存到: {output_path}")

    except Exception as e:
        print(f"\n[FAILED] 增强失败: {e}")


def interactive_test():
    """交互式测试"""
    print("\n" + "=" * 60)
    print("交互式图生图测试")
    print("=" * 60)

    # 查找测试图片
    tmp_dir = Path("tmp")
    test_images = list(tmp_dir.glob("calendar_*.png")) + list(tmp_dir.glob("calendar_*.jpg"))

    if not test_images:
        print(f"错误: 未找到测试图片")
        print("请确保 tmp 文件夹下有 calendar_*.png 或 calendar_*.jpg 文件")
        return

    # 使用最新的图片
    test_image_path = sorted(test_images)[-1]
    print(f"\n将使用图片: {test_image_path}")

    base_image = Image.open(test_image_path)
    print(f"图片尺寸: {base_image.size}")

    # 加载配置
    config = configparser.ConfigParser()
    config_path = Path("config.ini")
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        return

    config.read(config_path, encoding="utf-8")

    api_key = config.get("api", "api_key", fallback=None)
    base_url = config.get("generation", "base_url", fallback="https://aihubmix.com/v1")
    model = config.get("generation", "model", fallback="gemini-2.5-flash-image")

    if not api_key:
        print("错误: 未配置 API Key")
        return

    # 生成提示词预览
    prompt = build_img2img_prompt()
    print(f"\n生成的精绘提示词 (长度: {len(prompt)} 字符):")
    print("-" * 60)
    print(prompt)
    print("-" * 60)

    # 确认是否继续
    confirm = input("\n是否继续调用 API 进行增强? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    try:
        print(f"\n正在调用 {model} 进行增强...")
        enhanced_data = enhance_with_img2img(
            base_image=base_image,
            style_prompt=prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

        # 保存结果
        output_dir = Path("tmp/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"interactive_{test_image_path.stem}.png"
        save_image(enhanced_data, output_path)
        print(f"\n✓ 增强成功! 结果已保存到: {output_path}")

    except Exception as e:
        print(f"\n✗ 增强失败: {e}")


if __name__ == "__main__":
    import sys

    print("图生图精绘测试工具")
    print("=" * 60)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "prompt":
            # 仅测试提示词生成
            test_prompt_generation()

        elif command == "enhance":
            # 测试完整的增强流程
            test_img2img_enhancement()

        elif command == "interactive":
            # 交互式测试
            interactive_test()

        else:
            print(f"未知命令: {command}")
            print("\n可用命令:")
            print("  uv run python test_img2img.py prompt       - 查看精绘提示词")
            print("  uv run python test_img2img.py enhance      - 测试图生图增强")
            print("  uv run python test_img2img.py interactive  - 交互式测试")
    else:
        print("\n可用命令:")
        print("  uv run python test_img2img.py prompt       - 查看精绘提示词")
        print("  uv run python test_img2img.py enhance      - 测试图生图增强")
        print("  uv run python test_img2img.py interactive  - 交互式测试")

        # 默认执行提示词测试
        print("\n默认执行提示词生成测试...")
        test_prompt_generation()
