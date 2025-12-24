#!/usr/bin/env python3
"""
日历渲染模块
使用 Pillow + calendar 绘制基础日历图片
"""

import calendar
import configparser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont


def _load_renderer_config() -> Dict[str, Any]:
    """从 config.ini 加载渲染器配置"""
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent / "config.ini"

    defaults = {
        "cell_width": 75,
        "cell_height": 70,
        "single_month_width": 800,
        "multi_month_width": 1000,
        "single_month_content_height": 500,
        "multi_month_content_height": 600,
    }

    if config_path.exists():
        config.read(config_path, encoding="utf-8")
        if "renderer" in config:
            for key in defaults:
                if key in config["renderer"]:
                    defaults[key] = config["renderer"].getint(key)

    return defaults


class CalendarRenderer:
    """
    使用 Pillow + calendar 绘制基础日历

    设计原则：
    - 简洁的基础布局，依赖图生图 API 进行美化
    - 清晰显示所有假期信息
    - 跨平台中文字体支持
    - 根据月份数量动态调整宽度
    """

    # 默认配置（颜色）
    DEFAULT_HEIGHT = 900
    DEFAULT_BG_COLOR = (255, 255, 255)      # 白色背景
    DEFAULT_TEXT_COLOR = (30, 30, 30)       # 深灰色文字（比纯黑更柔和）
    DEFAULT_HOLIDAY_COLOR = (220, 60, 60)   # 红色标记放假
    DEFAULT_MAKEUP_COLOR = (80, 120, 200)   # 蓝色标记调休
    DEFAULT_GRID_COLOR = (200, 200, 200)    # 网格线颜色

    # 加载配置
    _renderer_config = _load_renderer_config()

    def __init__(self, holiday_data: Dict[str, Any]):
        """
        初始化渲染器

        Args:
            holiday_data: 从 parse_holiday_text 返回的 JSON 数据
        """
        self.data = holiday_data

        # 兼容新旧两种数据格式
        # 新格式: [{"date": "2026-02-12", "type": "holiday"}, ...]
        # 旧格式: ["2026-02-12", "2026-02-13", ...]
        holiday_dates_raw = holiday_data.get("holiday_dates", [])
        self.holiday_set = set()
        for item in holiday_dates_raw:
            if isinstance(item, dict):
                self.holiday_set.add(item["date"])
            else:
                self.holiday_set.add(item)

        # 构建调休日期字典（兼容新旧格式）
        self.makeup_days = {}
        for m in holiday_data.get("makeup_workdays", []):
            if isinstance(m, dict):
                self.makeup_days[m["date"]] = m.get("description", "调休上班")
            else:
                self.makeup_days[m] = "调休上班"

    def _get_font(self, size: int = 20, bold: bool = False) -> ImageFont.FreeTypeFont:
        """
        获取字体，支持中文

        跨平台字体检测，按优先级尝试以下字体：
        - Windows: 微软雅黑, 黑体, 宋体
        - Linux: WenQuanYi Microhei, Noto Sans CJK
        - macOS: PingFang SC, STHeiti

        Args:
            size: 字体大小
            bold: 是否使用粗体

        Returns:
            ImageFont: 可用的字体对象
        """
        font_names = [
            # Windows 字体
            "msyhbd.ttc" if bold else "msyh.ttc",      # 微软雅黑
            "simhei.ttf",                              # 黑体
            "simsun.ttc",                              # 宋体
            # Linux 字体
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            # macOS 字体
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]

        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except OSError:
                continue

        # 回退到默认字体
        return ImageFont.load_default()

    def _draw_text_with_fallback(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int],
        anchor: str = "lt"
    ) -> None:
        """
        绘制文本，处理中文显示问题

        Args:
            draw: ImageDraw 对象
            text: 要绘制的文本
            position: 位置坐标 (x, y)
            font: 字体对象
            color: 文字颜色
            anchor: 锚点位置
        """
        try:
            draw.text(position, text, fill=color, font=font, anchor=anchor)
        except Exception as e:
            # 如果绘制失败，尝试使用默认字体
            default_font = ImageFont.load_default()
            draw.text(position, text, fill=color, font=default_font, anchor=anchor)

    def _draw_month_calendar(
        self,
        draw: ImageDraw.ImageDraw,
        year: int,
        month: int,
        x: int,
        y: int,
        cell_width: int = None,
        cell_height: int = None
    ) -> int:
        """
        绘制单月日历

        Args:
            draw: ImageDraw 对象
            year: 年份
            month: 月份
            x: 起始 X 坐标
            y: 起始 Y 坐标
            cell_width: 单元格宽度（默认从配置读取）
            cell_height: 单元格高度（默认从配置读取）

        Returns:
            int: 占用的总高度
        """
        if cell_width is None:
            cell_width = self._renderer_config["cell_width"]
        if cell_height is None:
            cell_height = self._renderer_config["cell_height"]

        cal = calendar.monthcalendar(year, month)
        month_name = f"{year}年{month}月"
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]

        # 绘制月份标题
        title_font = self._get_font(26, bold=True)
        self._draw_text_with_fallback(
            draw, month_name, (x, y), title_font, self.DEFAULT_TEXT_COLOR
        )
        y += 40

        # 绘制星期标题
        weekday_font = self._get_font(16)
        for i, wd in enumerate(weekdays):
            # 周末用红色突出
            color = self.DEFAULT_HOLIDAY_COLOR if i >= 5 else self.DEFAULT_TEXT_COLOR
            # 居中显示
            text_x = x + i * cell_width + cell_width // 2
            self._draw_text_with_fallback(
                draw, wd, (text_x, y), weekday_font, color, anchor="mt"
            )
        y += 30

        # 绘制日期网格
        date_font = self._get_font(18)
        label_font = self._get_font(12)

        for week in cal:
            for i, day in enumerate(week):
                if day == 0:
                    continue

                cell_x = x + i * cell_width
                cell_y = y

                # 绘制单元格边框
                draw.rectangle(
                    [cell_x, cell_y, cell_x + cell_width, cell_y + cell_height],
                    outline=self.DEFAULT_GRID_COLOR,
                    width=1
                )

                # 构造日期字符串
                date_str = f"{year}-{month:02d}-{day:02d}"

                # 确定日期颜色和标记
                color = self.DEFAULT_TEXT_COLOR
                label = ""

                if date_str in self.holiday_set:
                    color = self.DEFAULT_HOLIDAY_COLOR
                    label = "休"
                elif date_str in self.makeup_days:
                    color = self.DEFAULT_MAKEUP_COLOR
                    label = "班"

                # 绘制日期数字（左上角）
                self._draw_text_with_fallback(
                    draw, str(day), (cell_x + 8, cell_y + 8), date_font, color
                )

                # 绘制标记（右下角）
                if label:
                    self._draw_text_with_fallback(
                        draw, label,
                        (cell_x + cell_width - 8, cell_y + cell_height - 8),
                        label_font, color, anchor="rd"
                    )

            y += cell_height

        return y - (y - len(cal) * cell_height - 70)  # 返回实际占用高度

    def render(
        self,
        width: int = None,
        height: int = DEFAULT_HEIGHT,
        output_path: Optional[Path] = None
    ) -> Image.Image:
        """
        渲染完整的日历图片

        布局说明：
        - 顶部：节假日标题
        - 信息区：日期范围、总天数、调休安排
        - 日历区：月历网格

        Args:
            width: 图片宽度（None 表示根据月份数量自动计算）
            height: 图片高度
            output_path: 可选的保存路径

        Returns:
            PIL.Image: 渲染后的图片
        """
        # 动态计算宽度
        if width is None:
            calendar_months = self.data.get("calendar_months")
            if not calendar_months:
                # 尝试从 month 字段获取
                if "month" in self.data:
                    calendar_months = [self.data["month"]]
                else:
                    # 从 start_date 中提取月份
                    start_date = self.data.get("start_date")
                    if start_date:
                        month = datetime.fromisoformat(start_date).month
                        calendar_months = [month]
                    else:
                        calendar_months = [1]

            # 根据月份数量选择宽度
            if len(calendar_months) == 1:
                width = self._renderer_config["single_month_width"]
            else:
                width = self._renderer_config["multi_month_width"]

        # 创建图片
        img = Image.new("RGB", (width, height), self.DEFAULT_BG_COLOR)
        draw = ImageDraw.Draw(img)

        y_offset = 20

        # 绘制标题
        title_font = self._get_font(36, bold=True)
        title = self.data.get("holiday_name", "假日日历")
        self._draw_text_with_fallback(
            draw, title, (20, y_offset), title_font, self.DEFAULT_TEXT_COLOR
        )
        y_offset += 55

        # 绘制日期范围信息
        info_font = self._get_font(20)
        info_text = (
            f"放假时间: {self.data['start_date']} 至 {self.data['end_date']} "
            f"(共{self.data['total_days']}天)"
        )
        self._draw_text_with_fallback(
            draw, info_text, (20, y_offset), info_font, self.DEFAULT_TEXT_COLOR
        )
        y_offset += 35

        # 绘制调休信息
        if self.data.get("makeup_workdays"):
            self._draw_text_with_fallback(
                draw, "调休安排:", (20, y_offset), info_font, self.DEFAULT_TEXT_COLOR
            )
            y_offset += 30

            makeup_font = self._get_font(16)
            for makeup in self.data["makeup_workdays"]:
                makeup_text = f"  {makeup['date']}: {makeup.get('description', '调休上班')}"
                self._draw_text_with_fallback(
                    draw, makeup_text, (20, y_offset), makeup_font, self.DEFAULT_MAKEUP_COLOR
                )
                y_offset += 25
            y_offset += 10

        # 绘制额外备注
        if self.data.get("notes"):
            note_font = self._get_font(16)
            note_color = (100, 100, 100)  # 灰色
            self._draw_text_with_fallback(
                draw, f"备注: {self.data['notes']}", (20, y_offset), note_font, note_color
            )
            y_offset += 30

        # 绘制月份日历
        # 兼容新旧格式：如果没有 calendar_months，从 month 或 start_date 中提取
        calendar_months = self.data.get("calendar_months")
        if not calendar_months:
            # 尝试从 month 字段获取
            if "month" in self.data:
                calendar_months = [self.data["month"]]
            else:
                # 从 start_date 中提取月份
                from datetime import datetime
                start_date = self.data.get("start_date")
                if start_date:
                    month = datetime.fromisoformat(start_date).month
                    calendar_months = [month]
                else:
                    calendar_months = [1]  # 默认值

        # 如果需要显示多个月份，使用两列布局
        if len(calendar_months) > 2:
            col1_x = 20
            col2_x = width // 2 + 20
            current_y = y_offset

            for i, month in enumerate(calendar_months):
                if i % 2 == 0:
                    x_pos = col1_x
                else:
                    x_pos = col2_x

                if i % 2 == 0 and i > 0:
                    current_y = y_offset  # 换行回到顶部

                self._draw_month_calendar(
                    draw, self.data["year"], month, x_pos, current_y
                )

                if i % 2 == 1:
                    current_y += 350  # 下一个位置
        else:
            # 单列布局
            for month in calendar_months:
                if y_offset + 350 > height:
                    # 动态调整高度
                    new_height = y_offset + 400
                    new_img = Image.new("RGB", (width, new_height), self.DEFAULT_BG_COLOR)
                    new_img.paste(img)
                    img = new_img
                    draw = ImageDraw.Draw(img)

                self._draw_month_calendar(
                    draw, self.data["year"], month, 20, y_offset
                )
                y_offset += 350

        # 裁剪到实际内容大小
        final_img = img.crop((0, 0, width, y_offset))

        # 可选：保存到文件
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_img.save(output_path)
            print(f"基础日历已保存: {output_path}")

        return final_img


def main():
    """测试日历渲染器"""
    # 示例数据
    test_data = {
        "holiday_name": "2025年春节",
        "year": 2025,
        "month": 1,
        "start_date": "2025-01-28",
        "end_date": "2025-02-04",
        "total_days": 8,
        "holiday_dates": [
            "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
            "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04"
        ],
        "makeup_workdays": [
            {"date": "2025-01-26", "description": "周日上班"},
            {"date": "2025-02-08", "description": "周六上班"}
        ],
        "calendar_months": [1, 2],
        "notes": "春节期间高速免费"
    }

    renderer = CalendarRenderer(test_data)
    img = renderer.render()
    img.show()


if __name__ == "__main__":
    main()
