#!/usr/bin/env python3
"""
图生图增强模块
使用 AI 对基础日历图片进行风格化处理
"""

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Optional

from openai import OpenAI
from PIL import Image

# 导入提示词模板
from prompts.templates import (
    IMG2IMG_CORE_PROMPT,
    IMG2IMG_NEGATIVE_PROMPT,
    IMG2IMG_STYLE_PRESETS,
    STYLE_PRESETS,
)


def build_img2img_prompt(
    style: str = "国风水墨风",
    custom_instruction: str = "",
    use_new_template: bool = True
) -> str:
    """
    构造图生图的提示词

    新版提示词采用三层结构：
    1. 核心提示词：确保所有关键信息被保留
    2. 风格修饰词：应用指定的艺术风格
    3. 反向提示词：避免生成错误内容

    Args:
        style: 风格预设名称（建议使用新版风格：国风水墨风、现代插画风、可爱3D风、简约商务风）
        custom_instruction: 自定义指令（会覆盖风格预设）
        use_new_template: 是否使用新版提示词模板（默认 True）

    Returns:
        str: 完整的图生图提示词
    """
    if use_new_template:
        # 使用新版三层结构提示词
        style_preset = IMG2IMG_STYLE_PRESETS.get(style, IMG2IMG_STYLE_PRESETS["国风水墨风"])
        style_modifiers = custom_instruction if custom_instruction else style_preset["style_modifiers"]

        prompt = f"""{IMG2IMG_CORE_PROMPT}

{style_modifiers}

**Quality Standards:**
- {IMG2IMG_NEGATIVE_PROMPT} (avoid these)
- High resolution, sharp details
- Professional composition and balance
- Consistent lighting and color harmony
"""
    else:
        # 使用旧版提示词（向后兼容）
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


def get_available_img2img_styles() -> dict[str, str]:
    """
    获取所有可用的图生图风格预设

    Returns:
        dict: 风格名称到描述的映射
    """
    return {name: preset["description"] for name, preset in IMG2IMG_STYLE_PRESETS.items()}


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
    使用 Gemini 2.5 Flash Image 对基础日历图片进行风格化处理

    根据 AiHubMix 文档，使用 OpenAI 兼容方式调用 Gemini 图生图功能
    注意：gemini-3-pro-image-preview 在 AiHubMix 上存在兼容性问题

    Args:
        base_image: PIL Image 对象（基础日历）
        style_prompt: 风格化提示词
        api_key: API Key
        base_url: API 基础 URL（默认为 AiHubMix OpenAI 兼容端点）
        model: 使用的模型（默认 gemini-2.5-flash-image，稳定版图像生成模型）

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
    print(f"提示词长度: {len(style_prompt)} 字符")

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

        # 解析响应 - 检查多种可能的返回格式
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            message = choice.message

            # 方法1: 检查 multi_mod_content 字段（OpenAI SDK 格式）
            if hasattr(message, 'multi_mod_content') and message.multi_mod_content:
                for mod in message.multi_mod_content:
                    # mod 可能是对象或字典
                    if isinstance(mod, dict):
                        if 'inline_data' in mod and mod['inline_data']:
                            image_data = mod['inline_data'].get('data')
                            mime_type = mod['inline_data'].get('mime_type', 'image/png')
                            if image_data:
                                print(f"找到图片数据 (multi_mod_content dict)，MIME 类型: {mime_type}")
                                return base64.b64decode(image_data)
                    elif hasattr(mod, 'inline_data') and mod.inline_data:
                        image_data = mod.inline_data.data
                        mime_type = mod.inline_data.mime_type
                        print(f"找到图片数据 (multi_mod_content)，MIME 类型: {mime_type}")
                        return base64.b64decode(image_data)

            # 方法2: 使用 model_dump 获取完整数据并解析
            if hasattr(message, 'model_dump'):
                dump = message.model_dump()
                if 'multi_mod_content' in dump and dump['multi_mod_content']:
                    for mod in dump['multi_mod_content']:
                        if isinstance(mod, dict) and 'inline_data' in mod:
                            inline_data = mod['inline_data']
                            if isinstance(inline_data, dict) and 'data' in inline_data:
                                image_data = inline_data['data']
                                mime_type = inline_data.get('mime_type', 'image/png')
                                if image_data:
                                    print(f"找到图片数据 (model_dump)，MIME 类型: {mime_type}")
                                    return base64.b64decode(image_data)

            # 方法3: 检查 content 字段是否是 JSON 格式
            if hasattr(message, 'content') and message.content:
                try:
                    content = json.loads(message.content)
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and 'inlineData' in item:
                                data = item['inlineData'].get('data')
                                mime_type = item['inlineData'].get('mimeType', 'image/png')
                                if data:
                                    print(f"找到图片数据 (JSON 格式)，MIME 类型: {mime_type}")
                                    return base64.b64decode(data)
                except json.JSONDecodeError:
                    pass

            # 方法4: 打印完整的响应结构用于调试
            print(f"完整响应结构:\n{json.dumps(dump, indent=2, ensure_ascii=False)[:1000]}...")

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
    style: str,
    custom_instruction: str,
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
        style: 风格预设名称
        custom_instruction: 自定义指令
        api_key: API Key
        output_path: 输出文件路径
        base_url: API 基础 URL
        model: 使用的模型

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
    )
    save_image(image_data, output_path)
    return output_path
