#!/usr/bin/env python3
"""
测试新的图生图提示词模板

使用 tmp 文件夹下的 calendar_web_20251224_103100.png 进行测试
"""

import configparser
from pathlib import Path
from PIL import Image

# 导入配置和函数
from img2img import (
    build_img2img_prompt,
    get_available_img2img_styles,
    enhance_with_img2img,
    save_image,
)


def test_prompt_generation():
    """测试提示词生成"""
    print("=" * 60)
    print("测试提示词生成")
    print("=" * 60)

    # 显示可用风格
    styles = get_available_img2img_styles()
    print("\n可用的图生图风格:")
    for name, desc in styles.items():
        print(f"  - {name}: {desc}")

    # 测试生成不同风格的提示词
    test_styles = ["国风水墨风", "现代插画风", "可爱3D风", "简约商务风"]

    for style in test_styles:
        print(f"\n{'=' * 60}")
        print(f"生成风格: {style}")
        print(f"{'=' * 60}")
        prompt = build_img2img_prompt(style=style, use_new_template=True)
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"提示词预览:\n{prompt[:500]}...")
        print()


def test_img2img_enhancement():
    """测试图生图增强功能"""
    print("\n" + "=" * 60)
    print("测试图生图增强")
    print("=" * 60)

    # 加载测试图片
    test_image_path = Path("tmp/calendar_web_20251224_103100.png")

    if not test_image_path.exists():
        print(f"错误: 测试图片不存在: {test_image_path}")
        print("请确保 tmp 文件夹下有 calendar_web_20251224_103100.png 文件")
        return

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
    # 使用 OpenAI 兼容端点
    base_url = config.get("generation", "base_url", fallback="https://aihubmix.com/v1")
    # 使用 Gemini 2.5 Flash Image Preview 模型
    model = config.get("generation", "model", fallback="gemini-2.5-flash-image-preview")

    if not api_key:
        print("错误: 未配置 API Key")
        return

    # 测试不同风格
    test_styles = [
        ("国风水墨风", "test_ink_wash"),
        ("现代插画风", "test_modern_illustration"),
        ("可爱3D风", "test_cute_3d"),
        ("简约商务风", "test_minimalist_business"),
    ]

    output_dir = Path("tmp/output")

    for style_name, output_suffix in test_styles:
        print(f"\n{'=' * 60}")
        print(f"测试风格: {style_name}")
        print(f"{'=' * 60}")

        # 构建提示词
        prompt = build_img2img_prompt(style=style_name, use_new_template=True)
        print(f"提示词已构建 (长度: {len(prompt)} 字符)")

        try:
            # 调用图生图 API
            print(f"正在调用 {model} 进行增强...")
            enhanced_data = enhance_with_img2img(
                base_image=base_image,
                style_prompt=prompt,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )

            # 保存结果
            output_path = output_dir / f"enhanced_{output_suffix}.png"
            save_image(enhanced_data, output_path)
            print(f"[SUCCESS] 增强成功! 结果已保存到: {output_path}")

        except Exception as e:
            print(f"[FAILED] 增强失败: {e}")
            continue


def interactive_test():
    """交互式测试"""
    print("\n" + "=" * 60)
    print("交互式图生图测试")
    print("=" * 60)

    # 显示可用风格
    styles = get_available_img2img_styles()
    print("\n可用的图生图风格:")
    for idx, (name, desc) in enumerate(styles.items(), 1):
        print(f"  {idx}. {name}: {desc}")

    # 选择风格
    try:
        choice = int(input("\n请选择风格 (输入序号): "))
        style_name = list(styles.keys())[choice - 1]
    except (ValueError, IndexError):
        print("无效的选择，使用默认风格: 国风水墨风")
        style_name = "国风水墨风"

    print(f"\n已选择风格: {style_name}")

    # 加载测试图片
    test_image_path = Path("tmp/calendar_web_20251224_103100.png")
    if not test_image_path.exists():
        print(f"错误: 测试图片不存在: {test_image_path}")
        return

    base_image = Image.open(test_image_path)
    print(f"已加载图片: {test_image_path} (尺寸: {base_image.size})")

    # 加载配置
    config = configparser.ConfigParser()
    config_path = Path("config.ini")
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        return

    config.read(config_path, encoding="utf-8")

    api_key = config.get("api", "api_key", fallback=None)
    # 使用 OpenAI 兼容端点
    base_url = config.get("generation", "base_url", fallback="https://aihubmix.com/v1")
    # 使用 Gemini 2.5 Flash Image Preview 模型
    model = config.get("generation", "model", fallback="gemini-2.5-flash-image-preview")

    if not api_key:
        print("错误: 未配置 API Key")
        return

    # 生成提示词预览
    prompt = build_img2img_prompt(style=style_name, use_new_template=True)
    print(f"\n生成的提示词 (长度: {len(prompt)} 字符):")
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
        output_path = output_dir / f"interactive_{style_name}.png"
        save_image(enhanced_data, output_path)
        print(f"\n✓ 增强成功! 结果已保存到: {output_path}")

    except Exception as e:
        print(f"\n✗ 增强失败: {e}")


if __name__ == "__main__":
    import sys

    print("图生图提示词测试工具")
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
            print("  python test_img2img.py prompt       - 测试提示词生成")
            print("  python test_img2img.py enhance      - 测试图生图增强")
            print("  python test_img2img.py interactive  - 交互式测试")
    else:
        print("\n可用命令:")
        print("  python test_img2img.py prompt       - 测试提示词生成")
        print("  python test_img2img.py enhance      - 测试图生图增强")
        print("  python test_img2img.py interactive  - 交互式测试")

        # 默认执行提示词测试
        print("\n默认执行提示词生成测试...")
        test_prompt_generation()
