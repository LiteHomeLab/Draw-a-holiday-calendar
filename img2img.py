#!/usr/bin/env python3
"""
图生图增强模块
使用 AI 对基础日历图片进行精绘处理
"""

import base64
import json
from io import BytesIO
from pathlib import Path

from openai import OpenAI
from PIL import Image

# 导入精绘提示词
from prompts.templates import FULL_PROMPT


def build_img2img_prompt() -> str:
    """
    获取图生图的精绘提示词

    使用统一的通用高质量精绘风格，无需选择风格。

    Returns:
        str: 完整的图生图精绘提示词
    """
    return FULL_PROMPT


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    将 PIL Image 转换为 Base64 字符串

    Args:
        image: PIL Image 对象
        format: 图片格式 (PNG, JPEG, etc.)

    Returns:
        str: Base64 编码的图片字符串
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def enhance_with_img2img(
    base_image: Image.Image,
    style_prompt: str,
    api_key: str,
    base_url: str = "https://aihubmix.com/v1",
    model: str = "gemini-2.5-flash-image",
) -> bytes:
    """
    使用 Gemini 2.5 Flash Image 对基础日历图片进行精绘处理

    使用 OpenAI 兼容方式调用 Gemini 图生图功能

    Args:
        base_image: PIL Image 对象（基础日历）
        style_prompt: 精绘提示词
        api_key: API Key
        base_url: API 基础 URL（默认为 AiHubMix OpenAI 兼容端点）
        model: 使用的模型（默认 gemini-2.5-flash-image）

    Returns:
        bytes: 增强后的图片二进制数据

    Raises:
        RuntimeError: 当 API 调用失败或无法获取图片时
    """
    # 创建 OpenAI 客户端（AiHubMix OpenAI 兼容模式）
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 将图片转换为 Base64
    image_base64 = image_to_base64(base_image, "PNG")

    print(f"正在调用 {model} 进行图生图增强...")
    print(f"API 端点: {base_url}")

    try:
        # 使用 OpenAI 兼容方式调用 Gemini 图生图
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": style_prompt
                        }
                    ]
                }
            ],
            modalities=["text", "image"],  # 要求输出文本和图片
            temperature=0.7,
        )

        print("API 调用成功!")

        # 解析响应 - 使用 model_dump 方法（最可靠）
        if response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            if hasattr(message, 'model_dump'):
                dump = message.model_dump()
                if 'multi_mod_content' in dump and dump['multi_mod_content']:
                    for mod in dump['multi_mod_content']:
                        if isinstance(mod, dict) and 'inline_data' in mod:
                            inline_data = mod['inline_data']
                            if isinstance(inline_data, dict) and 'data' in inline_data:
                                image_data = inline_data['data']
                                if image_data:
                                    print("图片数据获取成功")
                                    return base64.b64decode(image_data)

        print("警告: 未找到图片数据")
        raise RuntimeError("未能从图生图 API 响应中获取图片数据")

    except Exception as e:
        print(f"API 调用异常: {e}")
        raise RuntimeError(f"图生图 API 调用失败: {e}")


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
    api_key: str,
    output_path: Path,
    base_url: str = "https://aihubmix.com/v1",
    model: str = "gemini-2.5-flash-image"
) -> Path:
    """
    增强图片并保存到文件

    这是一个便捷函数，组合了 prompt 构建和 API 调用

    Args:
        base_image: PIL Image 对象（基础日历）
        api_key: API Key
        output_path: 输出文件路径
        base_url: API 基础 URL
        model: 使用的模型

    Returns:
        Path: 保存的文件路径
    """
    prompt = build_img2img_prompt()
    image_data = enhance_with_img2img(
        base_image=base_image,
        style_prompt=prompt,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
    save_image(image_data, output_path)
    return output_path
