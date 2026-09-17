"""生成文字完全可控的 PNG 多模态 Benchmark 资料。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).parent
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


def base(title: str, subtitle: str, accent: str):
    image = Image.new("RGB", (1080, 1440), "#f4f6f9")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 60, 1010, 1380), radius=34, fill="white", outline="#e3e7ed", width=3)
    draw.rounded_rectangle((70, 60, 1010, 260), radius=34, fill=accent)
    draw.rectangle((70, 220, 1010, 260), fill=accent)
    draw.text((120, 105), title, font=font(48, True), fill="white")
    draw.text((120, 180), subtitle, font=font(25), fill="#eaf0ff")
    draw.rounded_rectangle((790, 100, 950, 155), radius=18, fill="#ffffff")
    draw.text((825, 111), "TEST", font=font(24, True), fill=accent)
    return image, draw


def rows(draw, values, start=330):
    y = start
    for label, value, emphasis in values:
        draw.text((120, y), label, font=font(25), fill="#7b8492")
        draw.text((390, y - 5), value, font=font(31, emphasis), fill="#172033")
        draw.line((120, y + 66, 950, y + 66), fill="#edf0f4", width=2)
        y += 112
    return y


def footer(draw, text):
    draw.rounded_rectangle((120, 1235, 950, 1315), radius=18, fill="#f2f5f9")
    draw.text((170, 1256), text, font=font(22), fill="#677184")


def railway_ticket():
    image, draw = base("测试电子客票", "铁路行程订单 · 合成测试资料", "#315ca8")
    rows(draw, [
        ("行程", "北京南 → 上海虹桥", True),
        ("车次", "G5", True),
        ("出发日期", "2026-11-17", True),
        ("开车时间", "07:00", True),
        ("席位", "二等座 05车 05A", False),
        ("票价", "¥553.00", True),
        ("乘车人", "张*明", False),
        ("订单状态", "已出票", True),
    ])
    footer(draw, "仅用于 TripPilot 多模态测试 · 非真实客票")
    image.save(OUT / "railway_ticket.png", optimize=True)


def hotel_order():
    image, draw = base("酒店预订确认", "上海浦江酒店 · 合成测试订单", "#8257a8")
    rows(draw, [
        ("入住日期", "2026-10-18", True),
        ("离店日期", "2026-10-20", True),
        ("房型", "舒适双床房", False),
        ("入住晚数", "2晚", False),
        ("订单金额", "¥1200.00", True),
        ("订单状态", "已确认", True),
        ("取消规则", "入住前24小时可取消", False),
        ("备注", "早餐需避开花生制品", False),
    ])
    footer(draw, "仅用于 TripPilot 多模态测试 · 非真实订单")
    image.save(OUT / "hotel_order.png", optimize=True)


def museum_reservation():
    image, draw = base("场馆预约凭证", "上海示例艺术馆 · 合成测试资料", "#187c72")
    rows(draw, [
        ("预约日期", "2026-10-12 周一", True),
        ("预约时段", "14:00-16:00", True),
        ("预约人数", "2人", False),
        ("票价", "免费", False),
        ("场馆状态", "周一闭馆", True),
        ("凭证状态", "预约无效", True),
        ("处理建议", "改选其他开放场馆", False),
    ])
    draw.rounded_rectangle((120, 1120, 950, 1200), radius=18, fill="#fff3e8", outline="#ffc78f")
    draw.text((165, 1142), "冲突提示：预约时段与闭馆规则冲突", font=font(25, True), fill="#b45e16")
    footer(draw, "仅用于 TripPilot 多模态测试 · 非真实凭证")
    image.save(OUT / "museum_reservation.png", optimize=True)


def weather_alert():
    image, draw = base("暴雨橙色预警", "杭州市气象信息 · 合成测试资料", "#d36a24")
    rows(draw, [
        ("生效日期", "2026-11-21", True),
        ("生效时间", "08:00", True),
        ("预计持续", "08:00-18:00", False),
        ("影响区域", "西湖及周边区域", False),
        ("运营变化", "西湖游船暂停运营", True),
        ("风险提示", "避免长时间室外活动", True),
        ("建议", "调整为室内行程", False),
    ])
    footer(draw, "仅用于 TripPilot 多模态测试 · 非实时预警")
    image.save(OUT / "weather_alert.png", optimize=True)


def beijing_constraint_card():
    image, draw = base("北京行程约束卡", "用户确认信息 · 合成测试资料", "#356a54")
    rows(draw, [
        ("旅行天数", "3天", True),
        ("同行人数", "2人", False),
        ("总预算", "¥3600.00", True),
        ("每日强度", "最多2个景点", True),
        ("可游览时段", "09:00-18:00", False),
        ("交通偏好", "公共交通", False),
        ("兴趣偏好", "历史文化、博物馆", False),
        ("健康约束", "花生严重过敏", True),
    ])
    footer(draw, "用于稳定演示 · 实时事实仍须通过工具核验")
    image.save(OUT / "beijing_constraint_card.png", optimize=True)


if __name__ == "__main__":
    railway_ticket()
    hotel_order()
    museum_reservation()
    weather_alert()
    beijing_constraint_card()
    print("generated 5 PNG fixtures")
