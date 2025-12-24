#!/usr/bin/env python3
"""
放假通知文本解析模块 - OpenAI 兼容 API 版本
使用 OpenAI 兼容 API (如 deepseek-v3.2) 将放假文字描述解析为结构化 JSON 数据
"""

import json
import re
from typing import Any, Dict

from openai import OpenAI

# JSON Schema 定义
HOLIDAY_SCHEMA = {
    "type": "object",
    "properties": {
        "holiday_name": {"type": "string", "description": "节假日名称"},
        "year": {"type": "integer", "description": "年份"},
        "month": {"type": "integer", "description": "主要放假月份"},
        "start_date": {"type": "string", "format": "date", "description": "开始日期 (YYYY-MM-DD)"},
        "end_date": {"type": "string", "format": "date", "description": "结束日期 (YYYY-MM-DD)"},
        "total_days": {"type": "integer", "description": "总天数"},
        "holiday_dates": {
            "type": "array",
            "items": {"type": "string", "format": "date"},
            "description": "所有放假日期列表 (YYYY-MM-DD)"
        },
        "makeup_workdays": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"},
                    "description": {"type": "string"}
                }
            },
            "description": "调休安排（需要上班的周末）"
        },
        "calendar_months": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "需要显示的月份列表"
        },
        "notes": {"type": "string", "description": "额外备注信息"}
    },
    "required": ["holiday_name", "year", "month", "start_date", "end_date", "total_days", "holiday_dates"]
}

# 解析提示词模板
PARSER_PROMPT = """你是一个专业的放假通知解析助手。请从用户提供的放假通知文本中提取结构化信息，并严格按照 JSON Schema 返回数据。

**重要要求：**
1. 只返回纯 JSON 格式，不要包含任何解释文字
2. 日期格式必须是 YYYY-MM-DD
3. holiday_dates 必须包含从 start_date 到 end_date 之间的所有放假日期
4. 如果有调休安排，必须包含在 makeup_workdays 中
5. calendar_months 应该包含日历需要显示的所有月份

JSON Schema:
{schema}

放假通知文本：
{holiday_text}

请直接返回 JSON数据（不要使用代码块标记）：
"""


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    从 AI 响应中提取 JSON 数据

    处理多种可能的格式：
    - 纯 JSON
    - Markdown 代码块包裹的 JSON (```json ... ```)
    - 其他格式包裹的 JSON
    """
    text = text.strip()

    # 尝试去除 markdown 代码块标记
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",  # ```json ... ```
        r"```\s*([\s\S]*?)\s*```",      # ``` ... ```
        r"\{[\s\S]*\}",                 # 直接查找 JSON 对象
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            json_text = match.group(1) if match.lastindex else match.group(0)
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                continue

    # 如果以上都失败，尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"无法从响应中提取有效的 JSON 数据: {e}\n原始文本: {text}")


def parse_holiday_text(
    holiday_text: str,
    api_key: str,
    base_url: str = "https://aihubmix.com/v1",
    model: str = "deepseek-v3.2"
) -> Dict[str, Any]:
    """
    使用 OpenAI 兼容 API 解析放假通知文本，返回结构化的 JSON 数据

    API 调用格式参考用户提供的示例：
    ```python
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    ```

    Args:
        holiday_text: 放假通知文本
        api_key: API Key
        base_url: API 基础 URL (默认: https://aihubmix.com/v1)
        model: 使用的模型名称（默认: deepseek-v3.2）

    Returns:
        Dict: 包含假期信息的字典，包含以下字段：
            - holiday_name: 节假日名称
            - year: 年份
            - month: 月份
            - start_date: 开始日期 (YYYY-MM-DD)
            - end_date: 结束日期 (YYYY-MM-DD)
            - total_days: 总天数
            - holiday_dates: 放假日期列表
            - makeup_workdays: 调休安排列表
            - calendar_months: 需要显示的月份
            - notes: 额外备注

    Raises:
        ValueError: 当无法解析 JSON 数据时
        RuntimeError: 当 API 调用失败时
    """
    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = PARSER_PROMPT.format(
        schema=json.dumps(HOLIDAY_SCHEMA, ensure_ascii=False, indent=2),
        holiday_text=holiday_text
    )

    try:
        # 使用 OpenAI 兼容的 responses.create API
        response = client.responses.create(
            model=model,
            input=prompt,
        )

        # 提取并解析 JSON - 处理不同的响应格式
        if hasattr(response, 'output') and response.output:
            # GPT-5 风格的响应
            return _extract_json_from_text(response.output)
        elif hasattr(response, 'choices') and response.choices:
            # OpenAI ChatCompletion 风格的响应
            content = response.choices[0].message.content
            return _extract_json_from_text(content)
        else:
            # 兜底处理
            return _extract_json_from_text(str(response))

    except Exception as e:
        raise RuntimeError(f"解析放假通知失败: {e}")


def validate_holiday_data(data: Dict[str, Any]) -> bool:
    """
    验证解析后的假期数据是否完整有效

    Args:
        data: 解析后的假期数据字典

    Returns:
        bool: 数据是否有效

    Raises:
        ValueError: 当数据缺少必需字段或格式错误时
    """
    required_fields = [
        "holiday_name", "year", "month", "start_date",
        "end_date", "total_days", "holiday_dates"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"缺少必需字段: {field}")

    # 验证日期格式
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    for date_field in ["start_date", "end_date"]:
        if not re.match(date_pattern, data[date_field]):
            raise ValueError(f"{date_field} 日期格式错误，应为 YYYY-MM-DD")

    # 验证 holiday_dates 中的每个日期
    for date in data["holiday_dates"]:
        if not re.match(date_pattern, date):
            raise ValueError(f"holiday_dates 中的日期格式错误: {date}")

    # 验证 makeup_workdays 中的日期
    if "makeup_workdays" in data and data["makeup_workdays"]:
        for makeup in data["makeup_workdays"]:
            if "date" not in makeup:
                raise ValueError("makeup_workdays 中的项缺少 date 字段")
            if not re.match(date_pattern, makeup["date"]):
                raise ValueError(f"makeup_workdays 中的日期格式错误: {makeup['date']}")

    return True
