#!/usr/bin/env python3
"""
放假通知文本解析模块 - OpenAI 兼容 API 版本
使用 OpenAI 兼容 API (如 deepseek-v3.2) 将放假文字描述解析为结构化 JSON 数据

改进特性：
- 增强「补班」提取：识别「上班」「补班」「调休」关键词
- 增加日期校验：提取 weekday 用于画图前校验
- 扁平化数据结构：type 标记区分「休」/「班」
- 上下文增强：传入参考年份防止跨年错误
"""

import datetime
import json
import re
from typing import Any, Dict

from openai import OpenAI

# JSON Schema 定义（改进版）
HOLIDAY_SCHEMA = {
    "type": "object",
    "properties": {
        "holiday_name": {
            "type": "string",
            "description": "节假日名称，例如：五一劳动节"
        },
        "year": {
            "type": "integer",
            "description": "放假通知的年份"
        },
        "display_range": {
            "type": "string",
            "description": "放假时间的原始文本描述，例如：5月1日至5日放假调休"
        },
        "total_days": {
            "type": "integer",
            "description": "放假总天数"
        },
        "start_date": {
            "type": "string",
            "format": "date",
            "description": "放假开始日期 (YYYY-MM-DD)"
        },
        "end_date": {
            "type": "string",
            "format": "date",
            "description": "放假结束日期 (YYYY-MM-DD)"
        },
        "holiday_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"},
                    "weekday": {"type": "string", "description": "星期几，如：星期一"},
                    "type": {"type": "string", "enum": ["holiday"], "description": "固定为 holiday"}
                },
                "required": ["date"]
            },
            "description": "放假日期明细列表，包含开始到结束的所有每一天"
        },
        "makeup_workdays": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"},
                    "weekday": {"type": "string", "description": "星期几，如：星期六"},
                    "type": {"type": "string", "enum": ["work"], "description": "固定为 work"},
                    "description": {"type": "string", "description": "补班描述，例如：补5月4日(星期五)的班"}
                },
                "required": ["date", "type"]
            },
            "description": "调休补班/需要上班的周末日期列表。**这是重点，必须从文本中提取'上班'、'补班'相关的日期**"
        },
        "calendar_months": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "涉及到的月份数字列表，用于画图决定画几个月历"
        }
    },
    "required": ["holiday_name", "year", "holiday_dates", "makeup_workdays"]
}

# 解析提示词模板（改进版）
PARSER_PROMPT = """你是一个专业的节假日排班数据解析专家。你的任务是将非结构化的放假通知文本转换为下游画图工具可用的精确 JSON 数据。

**输入上下文：**
参考年份：{current_year} (如果文本中未指明年份，请默认使用此年份)
当前文本：
{holiday_text}

**解析步骤与规则（请严格遵守）：**

1. **日期计算逻辑：**
   - 必须算出 `start_date` 到 `end_date` 之间的每一天，填入 `holiday_dates` 数组。
   - **不要遗漏中间的日期**。例如：1日到5日，必须包含1,2,3,4,5号。

2. **补班（重点解析）：**
   - 仔细查找文本中包含 **"上班"、"补班"、"调休"** 字样的句子。
   - 通常格式为："X月X日（星期X）上班"。
   - 将这些日期提取到 `makeup_workdays` 数组中。
   - 如果文本中明确写了"无调休"或没提补班，该数组为空。
   - 确保补班日期的年份与放假年份一致。

3. **格式约束：**
   - 日期必须是 `YYYY-MM-DD` 格式。
   - `weekday` 字段请计算准确（星期一 至 星期日）。
   - 只返回纯 JSON，不要包含 Markdown 标记（```json ... ```）。

**目标 JSON Schema：**
{schema}

请直接返回 JSON 数据：
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


def _get_weekday(date_str: str) -> str:
    """
    计算给定日期的星期几（中文名称）

    Args:
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        str: 星期几的中文名称（如：星期一）
    """
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    return weekday_map[date_obj.weekday()]


def _correct_weekdays(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    自动纠正数据中的 weekday 字段

    使用 Python datetime 计算正确的星期几，覆盖 LLM 可能返回的错误值。

    Args:
        data: 解析后的假期数据

    Returns:
        Dict: weekday 字段被纠正后的数据
    """
    # 纠正 holiday_dates 中的 weekday
    if "holiday_dates" in data:
        for day_entry in data["holiday_dates"]:
            if "date" in day_entry:
                day_entry["weekday"] = _get_weekday(day_entry["date"])

    # 纠正 makeup_workdays 中的 weekday
    if "makeup_workdays" in data:
        for work_entry in data["makeup_workdays"]:
            if "date" in work_entry:
                work_entry["weekday"] = _get_weekday(work_entry["date"])

    return data


def parse_holiday_text(
    holiday_text: str,
    api_key: str,
    base_url: str = "https://aihubmix.com/v1",
    model: str = "deepseek-v3.2",
    current_year: int | None = None
) -> Dict[str, Any]:
    """
    使用 OpenAI 兼容 API 解析放假通知文本，返回结构化的 JSON 数据

    Args:
        holiday_text: 放假通知文本
        api_key: API Key
        base_url: API 基础 URL (默认: https://aihubmix.com/v1)
        model: 使用的模型名称（默认: deepseek-v3.2）
        current_year: 参考年份（默认为当前年份，用于处理文本中未指明年份的日期）

    Returns:
        Dict: 包含假期信息的字典，包含以下字段：
            - holiday_name: 节假日名称
            - year: 年份
            - display_range: 放假时间原始描述
            - total_days: 总天数
            - start_date: 开始日期 (YYYY-MM-DD)
            - end_date: 结束日期 (YYYY-MM-DD)
            - holiday_dates: 放假日期列表（每个元素包含 date/weekday/type）
            - makeup_workdays: 调休安排列表（每个元素包含 date/weekday/type/description）
            - calendar_months: 需要显示的月份

    Raises:
        ValueError: 当无法解析 JSON 数据时
        RuntimeError: 当 API 调用失败时
    """
    if current_year is None:
        current_year = datetime.datetime.now().year

    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = PARSER_PROMPT.format(
        schema=json.dumps(HOLIDAY_SCHEMA, ensure_ascii=False, indent=2),
        holiday_text=holiday_text,
        current_year=current_year
    )

    try:
        # 使用 OpenAI 兼容的 chat.completions.create API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # 提取并解析 JSON - OpenAI ChatCompletion 风格的响应
        content = response.choices[0].message.content
        data = _extract_json_from_text(content)

        # 自动纠正 weekday 字段
        data = _correct_weekdays(data)

        return data

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
        "holiday_name", "year", "holiday_dates", "makeup_workdays"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"缺少必需字段: {field}")

    # 验证日期格式
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"

    # 验证 start_date 和 end_date（如果存在）
    for date_field in ["start_date", "end_date"]:
        if date_field in data and data[date_field]:
            if not re.match(date_pattern, data[date_field]):
                raise ValueError(f"{date_field} 日期格式错误，应为 YYYY-MM-DD")

    # 验证 holiday_dates 中的每个日期项
    if not isinstance(data["holiday_dates"], list):
        raise ValueError("holiday_dates 必须是数组")

    for item in data["holiday_dates"]:
        if not isinstance(item, dict):
            raise ValueError("holiday_dates 中的项必须是对象")
        if "date" not in item:
            raise ValueError("holiday_dates 中的项缺少 date 字段")
        if not re.match(date_pattern, item["date"]):
            raise ValueError(f"holiday_dates 中的日期格式错误: {item['date']}")

    # 验证 makeup_workdays 中的每个日期项
    if not isinstance(data["makeup_workdays"], list):
        raise ValueError("makeup_workdays 必须是数组")

    for item in data["makeup_workdays"]:
        if not isinstance(item, dict):
            raise ValueError("makeup_workdays 中的项必须是对象")
        if "date" not in item:
            raise ValueError("makeup_workdays 中的项缺少 date 字段")
        if "type" not in item:
            raise ValueError("makeup_workdays 中的项缺少 type 字段")
        if not re.match(date_pattern, item["date"]):
            raise ValueError(f"makeup_workdays 中的日期格式错误: {item['date']}")
        if item["type"] != "work":
            raise ValueError(f"makeup_workdays 中的 type 必须是 'work'，实际为: {item['type']}")

    # 验证 calendar_months（如果存在）
    if "calendar_months" in data and data["calendar_months"]:
        if not isinstance(data["calendar_months"], list):
            raise ValueError("calendar_months 必须是数组")
        for month in data["calendar_months"]:
            if not isinstance(month, int) or month < 1 or month > 12:
                raise ValueError(f"calendar_months 中的月份无效: {month}")

    return True
