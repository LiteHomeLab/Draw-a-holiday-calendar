"""
提示词模板模块
图生图精绘提示词 - 统一通用高质量风格
"""

# 图生图核心提示词 - 统一精绘风格
# 基于 AI 最佳实践，明确"什么不变"和"允许改什么"
IMG2IMG_PROMPT = """Enhance and polish this UI design of a holiday calendar. The goal is to make it more elegant, modern, and professional.

**CRITICAL INSTRUCTIONS (MUST FOLLOW):**
1. **Strictly preserve the original layout and structure.** Do not move the header, metadata, or the calendar grid.
2. **Ensure 100% accuracy and legibility of all text and numbers.** All Chinese characters ("春节", "休", "班") and dates must be perfectly identical to the original image.
3. **Maintain the core color-coding logic:** a red mark for holidays ("休") and a blue mark for workdays ("班").

**Allowed enhancements:**
- Refine the color palette to be more harmonious and sophisticated.
- Improve typography for better visual hierarchy and elegance.
- Add subtle, soft drop shadows to the main card for a gentle sense of depth (Material Design or neumorphism lite).
- Replace the simple background gradient with a more refined, abstract, or soft-focus background.

**Keywords:** UI/UX design, minimalist, clean, sharp focus, high detail, Behance, Dribbble, professional graphic design.
"""

# 反向提示词 - 防止生成错误内容
NEGATIVE_PROMPT = """major layout changes, different text, incorrect numbers, wrong dates, illegible characters, distorted grid, blurry, pixelated, hand-drawn, cartoon, 3D render, photo, cluttered, messy, watermark, signature.
"""

# 完整提示词 - 组合核心提示词和反向提示词
FULL_PROMPT = f"""{IMG2IMG_PROMPT}

**Avoid:**
{NEGATIVE_PROMPT}
"""
