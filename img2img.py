#!/usr/bin/env python3
"""
图生图增强模块
使用 AI 对基础日历图片进行风格化处理
"""

from io import BytesIO
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

# 重用现有的风格预设
from prompts.templates import STYLE_PRESETS


def build_img2img_prompt(
    style: str = "简约商务风",
    custom_instruction: str = ""
) -> str:
    """
    构造图生图的提示词

    提示词告诉 AI：
    1. 保持所有日期信息的准确性
    2. 美化视觉效果，应用指定风格
    3. 保持日历布局清晰可读

    Args:
        style: 风格预设名称
        custom_instruction: 自定义指令（会覆盖风格预设）

    Returns:
        str: 完整的图生图提示词
    """
    style_instruction = custom_instruction if custom_instruction else STYLE_PRESETS.get(
        style, STYLE_PRESETS["简约商务风"]
    )

    prompt = f"""You are a professional graphic designer specializing in holiday calendar designs.

Please enhance and beautify this base calendar image while preserving ALL the essential information:
- Keep ALL dates accurate and readable
- Maintain the holiday date range information
- Preserve all makeup work day notes
- Keep the calendar layout clear and organized
- Do NOT change any factual information

Style Requirements:
{style_instruction}

Your task:
1. Enhance the visual appeal with better colors, fonts, and layout
2. Add appropriate decorative elements (icons, patterns, illustrations)
3. Improve typography for better readability
4. Apply the specified design style consistently throughout
5. Output a high-quality, professionally designed calendar image
6. Make the holiday information prominent and easy to understand

Remember: This is a functional calendar - accuracy is more important than artistic creativity.
"""
    return prompt


def enhance_with_img2img(
    base_image: Image.Image,
    style_prompt: str,
    api_key: str,
    base_url: str = "https://aihubmix.com/gemini",
    model: str = "gemini-2.5-flash-image",
    aspect_ratio: str = "16:9",
    resolution: str = "2K"
) -> bytes:
    """
    使用图生图 API 对基础日历图片进行风格化处理

    Args:
        base_image: PIL Image 对象（基础日历）
        style_prompt: 风格化提示词
        api_key: API Key
        base_url: API 基础 URL
        model: 使用的模型（默认 gemini-2.5-flash-image）
        aspect_ratio: 图片比例
        resolution: 分辨率

    Returns:
        bytes: 增强后的图片二进制数据

    Raises:
        RuntimeError: 当 API 调用失败或无法获取图片时
    """
    client = genai.Client(
        api_key=api_key,
        http_options={"base_url": base_url}
    )

    print(f"正在调用 {model} 进行图生图增强...")
    print(f"风格提示: {style_prompt[:100]}...")

    response = client.models.generate_content(
        model=model,
        contents=[style_prompt, base_image],
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
            print(f"AI 响应: {part.text[:200]}...")
        elif inline_data := part.inline_data:
            print("图片生成成功!")
            return inline_data.data

    raise RuntimeError("未能从图生图 API 响应中获取图片数据")


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    将 PIL Image 转换为字节流

    Args:
        image: PIL Image 对象
        format: 图片格式 (PNG, JPEG, etc.)

    Returns:
        bytes: 图片的二进制数据
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()


def bytes_to_image(data: bytes) -> Image.Image:
    """
    将字节流转换为 PIL Image

    Args:
        data: 图片的二进制数据

    Returns:
        PIL.Image: 图片对象
    """
    return Image.open(BytesIO(data))


def save_image(data: bytes, output_path: Path) -> None:
    """
    保存图片数据到文件

    Args:
        data: 图片二进制数据
        output_path: 输出文件路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"图片已保存: {output_path.absolute()}")


def enhance_and_save(
    base_image: Image.Image,
    style: str,
    custom_instruction: str,
    api_key: str,
    output_path: Path,
    base_url: str = "https://aihubmix.com/gemini",
    model: str = "gemini-2.5-flash-image",
    aspect_ratio: str = "16:9",
    resolution: str = "2K"
) -> Path:
    """
    增强图片并保存到文件

    这是一个便捷函数，组合了 prompt 构建和 API 调用

    Args:
        base_image: PIL Image 对象（基础日历）
        style: 风格预设名称
        custom_instruction: 自定义指令
        api_key: API Key
        output_path: 输出文件路径
        base_url: API 基础 URL
        model: 使用的模型
        aspect_ratio: 图片比例
        resolution: 分辨率

    Returns:
        Path: 保存的文件路径
    """
    prompt = build_img2img_prompt(style, custom_instruction)
    image_data = enhance_with_img2img(
        base_image=base_image,
        style_prompt=prompt,
        api_key=api_key,
        base_url=base_url,
        model=model,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
    )
    save_image(image_data, output_path)
    return output_path
