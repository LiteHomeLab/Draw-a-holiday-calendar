#!/usr/bin/env python3
"""
Web 渲染模块 - 使用 FullCalendar 生成美观的放假日历

设计思路：
- 生成静态 HTML 文件，内嵌 FullCalendar
- 使用 Playwright 自动打开浏览器截图
- 无需 Web 服务器，完全本地运行
- 根据月份数量动态调整宽度和宽高比
"""

import json
import tempfile
import configparser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.sync_api import sync_playwright


def _load_renderer_config() -> Dict[str, Any]:
    """从 config.ini 加载渲染器配置"""
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent / "config.ini"

    defaults = {
        "single_month_width": 800,
        "multi_month_width": 1000,
        "single_month_content_height": 500,
        "multi_month_content_height": 600,
        "aspect_ratio": 1.35,
    }

    if config_path.exists():
        config.read(config_path, encoding="utf-8")
        if "renderer" in config:
            for key in defaults:
                if key in config["renderer"]:
                    # aspect_ratio 是浮点数
                    if key == "aspect_ratio":
                        defaults[key] = config["renderer"].getfloat(key)
                    else:
                        defaults[key] = config["renderer"].getint(key)

    return defaults


class WebCalendarRenderer:
    """
    使用 FullCalendar 渲染放假日历

    工作流程：
    1. 根据 JSON 数据生成静态 HTML
    2. 使用 Playwright 打开 HTML
    3. 截图保存
    """

    # 类级别配置
    _renderer_config = _load_renderer_config()

    def __init__(self, holiday_data: Dict[str, Any]):
        """
        初始化渲染器

        Args:
            holiday_data: 从 parse_holiday_text 返回的 JSON 数据
        """
        self.data = holiday_data
        self.template_path = Path(__file__).parent / "templates" / "calendar_template.html"

    def _generate_html(self) -> str:
        """
        根据模板和数据生成 HTML 内容

        Returns:
            str: 生成的 HTML 内容
        """
        # 读取模板
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # 处理新格式的 holiday_dates (对象数组)
        holidays = self.data.get("holiday_dates", [])
        if holidays and isinstance(holidays[0], dict):
            holidays_list = holidays
        else:
            # 兼容旧格式 (字符串数组)
            holidays_list = [{"date": d} for d in holidays]

        # 处理新格式的 makeup_workdays
        workdays = self.data.get("makeup_workdays", [])

        # 计算徽章
        badges_html = ""
        if workdays:
            badges_html += f'<div class="info-item"><span class="badge badge-workday">补班 {len(workdays)} 天</span></div>'

        # 备注区域
        notes_html = ""
        if self.data.get("notes"):
            notes_html = f'<div class="notes"><div class="notes-text">备注: {self.data["notes"]}</div></div>'

        # 计算需要显示的月份
        calendar_months = self.data.get("calendar_months")
        if not calendar_months:
            if "month" in self.data:
                calendar_months = [self.data["month"]]
            else:
                start_date = self.data.get("start_date")
                if start_date:
                    month = datetime.fromisoformat(start_date).month
                    year = datetime.fromisoformat(start_date).year
                    calendar_months = [month]
                    # 检查是否需要包含下一个月
                    end_date = self.data.get("end_date")
                    if end_date:
                        end_month = datetime.fromisoformat(end_date).month
                        end_year = datetime.fromisoformat(end_date).year
                        if end_month != month or end_year != year:
                            calendar_months.append(end_month)
                else:
                    calendar_months = [1]

        # 去重并排序月份
        calendar_months = sorted(set(calendar_months))

        # 构建月份配置数据
        year = self.data.get("year", datetime.now().year)
        months_config = []
        for month in calendar_months:
            months_config.append({
                "year": year,
                "month": month,
                "initial_date": f"{year}-{month:02d}-01"
            })

        # 根据月份数量选择内容高度
        if len(calendar_months) == 1:
            content_height = self._renderer_config["single_month_content_height"]
        else:
            content_height = self._renderer_config["multi_month_content_height"]

        # 替换模板变量
        replacements = {
            "{{HOLIDAY_NAME}}": self.data.get("holiday_name", "假日日历"),
            "{{DISPLAY_RANGE}}": self.data.get("display_range", ""),
            "{{YEAR}}": str(year),
            "{{TOTAL_DAYS}}": str(self.data.get("total_days", 0)),
            "{{START_DATE}}": self.data.get("start_date", ""),
            "{{END_DATE}}": self.data.get("end_date", ""),
            "{{HOLIDAYS_JSON}}": json.dumps(holidays_list, ensure_ascii=False),
            "{{WORKDAYS_JSON}}": json.dumps(workdays, ensure_ascii=False),
            "{{BADGES_HTML}}": badges_html,
            "{{NOTES_HTML}}": notes_html,
            "{{ASPECT_RATIO}}": str(self._renderer_config["aspect_ratio"]),
            "{{CONTENT_HEIGHT}}": str(content_height),
            "{{MONTHS_COUNT}}": str(len(months_config)),
            "{{MONTHS_CONFIG}}": json.dumps(months_config, ensure_ascii=False),
        }

        html = template
        for key, value in replacements.items():
            html = html.replace(key, value)

        return html

    def render(
        self,
        output_path: Optional[Path] = None,
        width: int = None,
        height: int = 1000,
        save_html: bool = False,
        html_path: Optional[Path] = None
    ) -> Path:
        """
        渲染日历并截图

        Args:
            output_path: 截图保存路径（默认为临时文件）
            width: 浏览器视口宽度（None 表示根据月份数量自动计算）
            height: 浏览器视口高度
            save_html: 是否保存 HTML 文件
            html_path: HTML 文件保存路径

        Returns:
            Path: 截图文件的路径
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

        # 生成 HTML
        html_content = self._generate_html()

        # 保存 HTML（如果需要）
        if save_html and html_path is None:
            html_path = Path(tempfile.gettempdir()) / "holiday_calendar.html"

        if save_html and html_path:
            html_path.parent.mkdir(parents=True, exist_ok=True)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"HTML 已保存: {html_path}")

        # 创建临时 HTML 文件用于截图
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html_content)
            temp_html_path = f.name

        try:
            # 使用 Playwright 截图
            with sync_playwright() as p:
                # 启动浏览器
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": width, "height": height})

                # 加载 HTML
                page.goto(f"file:///{temp_html_path.replace(chr(92), '/')}")

                # 等待日历渲染完成
                page.wait_for_selector(".fc-daygrid-day", timeout=5000)

                # 设置输出路径
                if output_path is None:
                    output_path = Path(tempfile.gettempdir()) / "holiday_calendar.png"
                else:
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                # 截取整个 container 区域（包含 header、info-bar、calendar、notes）
                container_element = page.query_selector(".container")
                if container_element:
                    container_element.screenshot(path=str(output_path))
                else:
                    # 降级到全页面截图
                    page.screenshot(path=str(output_path), full_page=False)

                browser.close()

            print(f"日历截图已保存: {output_path}")
            return output_path

        finally:
            # 清理临时文件
            try:
                Path(temp_html_path).unlink()
            except:
                pass

    def generate_html_only(self, output_path: Path) -> None:
        """
        只生成 HTML 文件，不截图

        用户可以在浏览器中手动打开并截图

        Args:
            output_path: HTML 文件保存路径
        """
        html_content = self._generate_html()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML 已生成: {output_path}")
        print(f"请在浏览器中打开: file:///{output_path.as_posix()}")


def main():
    """测试 Web 渲染器"""
    # 示例数据（新格式）
    test_data = {
        "holiday_name": "2024年劳动节",
        "year": 2024,
        "display_range": "5月1日至5日放假调休",
        "total_days": 5,
        "start_date": "2024-05-01",
        "end_date": "2024-05-05",
        "holiday_dates": [
            {"date": "2024-05-01", "weekday": "星期三", "type": "holiday"},
            {"date": "2024-05-02", "weekday": "星期四", "type": "holiday"},
            {"date": "2024-05-03", "weekday": "星期五", "type": "holiday"},
            {"date": "2024-05-04", "weekday": "星期六", "type": "holiday"},
            {"date": "2024-05-05", "weekday": "星期日", "type": "holiday"}
        ],
        "makeup_workdays": [
            {"date": "2024-04-28", "weekday": "星期日", "type": "work", "description": "调休上班"},
            {"date": "2024-05-11", "weekday": "星期六", "type": "work", "description": "调休上班"}
        ],
        "calendar_months": [4, 5],
        "notes": "劳动节期间高速免费"
    }

    renderer = WebCalendarRenderer(test_data)

    # 只生成 HTML，用于手动测试
    renderer.generate_html_only(Path("test_calendar.html"))

    # 自动截图（需要安装 playwright）
    # renderer.render(save_html=True)


if __name__ == "__main__":
    main()
