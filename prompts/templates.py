"""
提示词模板模块
用于构造发送给 Gemini 3 Pro Image Preview 的提示词
"""

from typing import Dict, Optional


# 风格预设
STYLE_PRESETS: Dict[str, str] = {
    "简约商务风": """
Design a clean, minimalist business holiday calendar. Use black, white, and gray color scheme with subtle accent colors.
- Professional and elegant layout
- Clear typography, easy to read
- Minimalist icons and decorations
- Suitable for corporate communication
""",

    "现代多彩风": """
Design a modern, colorful holiday calendar. Use vibrant gradients and contemporary design elements.
- Bright, cheerful color palette
- Modern icons and illustrations
- Eye-catching visual elements
- Social media friendly style
""",

    "中国红喜庆风": """
Design a traditional Chinese holiday calendar with festive red and gold colors.
- Traditional Chinese aesthetic
- Red and gold color scheme
- Lanterns, clouds, or other traditional patterns as decorations
- Festive and celebratory atmosphere
""",

    "扁平化设计": """
Design a flat design holiday calendar. Use flat colors and simple geometric shapes.
- Flat UI design style
- Simple geometric shapes
- Solid colors without gradients
- Clean and modern appearance
""",
}


def build_prompt(holiday_text: str, style: str = "简约商务风", custom_instruction: str = "") -> str:
    """
    构造完整的提示词

    Args:
        holiday_text: 放假通知文本
        style: 风格预设名称
        custom_instruction: 自定义指令（会覆盖风格预设）

    Returns:
        完整的提示词字符串
    """
    style_instruction = custom_instruction if custom_instruction else STYLE_PRESETS.get(style, STYLE_PRESETS["简约商务风"])

    prompt = f"""Create a holiday calendar image based on the following holiday notice:

Holiday Notice:
{holiday_text}

Style Requirements:
{style_instruction}

Additional Instructions:
- Parse the holiday notice to extract exact dates and duration
- Display the calendar clearly showing all holiday dates
- Include a title indicating the holiday name
- Show the date range (start date to end date)
- Mark working days before/after the holiday if mentioned
- Use a clear grid layout for the calendar
- Include any special notes (e.g., makeup work days)
- Output should be a high-quality calendar image suitable for sharing
"""
    return prompt


def get_available_styles() -> list[str]:
    """获取所有可用的风格预设名称"""
    return list(STYLE_PRESETS.keys())
