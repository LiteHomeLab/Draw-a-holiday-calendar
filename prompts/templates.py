"""
提示词模板模块
用于构造发送给 Gemini 3 Pro Image Preview 的提示词
"""

from typing import Dict, Optional


# 风格预设（用于文生图）
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


# 图生图专用提示词模板
# 基于专业 AI 建议的三层结构：核心提示词 + 风格修饰词 + 反向提示词

# 核心提示词 - 确保所有关键信息被保留
IMG2IMG_CORE_PROMPT = """A beautifully designed calendar page for the Chinese New Year (Spring Festival), showing February 2026. The layout is clean, elegant, and highly readable.

**Key elements to preserve:**
- Main title in large Chinese characters: "春节" (chūnjié).
- A clear grid for the month of February 2026, with days of the week (Mon to Sun).
- All dates from 1 to 28 are clearly visible.
- **Holiday dates (Feb 12 to 25) are prominently marked in a festive red color**, each showing the Chinese character "休" (xiū, meaning "rest").
- **A make-up workday (Feb 27) is clearly marked in a distinct color like blue or grey**, showing the Chinese character "班" (bān, meaning "work").
- The overall aesthetic is celebratory but professional, suitable for a holiday announcement.

**Critical Requirements:**
- Perfectly rendered Chinese characters - all text must be 100% accurate
- Preserve ALL date information exactly as shown
- Do NOT change any factual information
- Award-winning graphic design, UI design, Behance, Dribbble, 4K, high detail
"""

# 反向提示词 - 避免生成错误内容
IMG2IMG_NEGATIVE_PROMPT = """blurry, fuzzy, distorted grid, warped text, illegible characters, incorrect Chinese characters, wrong dates, missing numbers, ugly, deformed, weird, watermark, signature, extra limbs, bad anatomy, cluttered, messy, photo, photorealistic"""

# 图生图风格预设 - 更详细的风格描述
IMG2IMG_STYLE_PRESETS: Dict[str, Dict[str, str]] = {
    "国风水墨风": {
        "style_modifiers": """
Style A: Traditional Chinese Ink Wash & Paper Art Style
- traditional Chinese painting style, ink wash (guohua), on textured rice paper (xuan paper)
- intricate papercraft, kirigami, layered paper art, diorama, soft shadows
- adorned with auspicious clouds (xiangyun), red lanterns, and subtle peony flower patterns
- The red '休' marks are in the style of a traditional cinnabar seal stamp
- warm color palette, imperial red, gold foil accents, dark ink
- Studio lighting casts soft shadows, giving it a 3D feel
""",
        "description": "传统水墨与纸艺风格，典雅精致"
    },

    "现代插画风": {
        "style_modifiers": """
Style B: Modern Flat Illustration & Animation Style
- modern flat illustration, vector art, graphic design, clean lines
- MG animation style, trendy, bold colors
- isometric illustration, cute, playful
- featuring festive elements like firecrackers and gold ingots (yuanbao)
- vibrant color palette, neon accents, high contrast, gradients
- The overall feeling is energetic and festive
""",
        "description": "现代扁平插画风格，色彩鲜明活泼"
    },

    "可爱3D风": {
        "style_modifiers": """
Style C: Cute 3D Clay & Plasticine Style
- charming 3D render, claymation style, plasticine art, soft and squishy
- Blender 3D, octane render, soft diffused lighting
- isometric 3D diorama
- decorated with cute miniature clay models of lanterns, lucky knots
- soft texture, matte finish
- The scene is lit with soft, warm lighting
""",
        "description": "可爱3D粘土风格，温暖有质感"
    },

    "简约商务风": {
        "style_modifiers": """
Style D: Minimalist Business Style
- clean, minimalist business design
- black, white, and gray color scheme with subtle accent colors
- Professional and elegant layout
- Clear typography, Sans-serif fonts
- Minimalist icons and decorations
- Suitable for corporate communication
""",
        "description": "简约商务风格，专业优雅"
    },
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
