#!/usr/bin/env python3
"""生成站点位图资产：og-card.png（1200×630 分享卡）与 apple-touch-icon.png（180×180）。

依赖 Pillow 与 macOS 系统字体（Songti.ttc / Menlo.ttc）；矢量 favicon 见 assets/favicon.svg。
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

PAPER = (246, 243, 235)
PAPER2 = (239, 234, 219)
INK = (34, 38, 31)
INK_SOFT = (87, 92, 79)
INK_FAINT = (134, 138, 123)
SAND = (201, 161, 118)
STAY = (169, 112, 54)
STAY_DEEP = (124, 80, 35)
STAY_DARK = (110, 71, 32)
RET = (58, 122, 110)
RET_DEEP = (37, 84, 73)


def load_font(path, size, want_names=()):
    """从 ttc 里按字体名挑选 face；找不到时退回 index 0。"""
    for idx in range(12):
        try:
            f = ImageFont.truetype(path, size, index=idx)
        except OSError:
            break
        name = " ".join(f.getname())
        if not want_names or any(w.lower() in name.lower() for w in want_names):
            return f
    return ImageFont.truetype(path, size, index=0)


SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"


def bezier(p0, p1, p2, p3, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def draw_polyline(draw, pts, fill, width):
    for a, b in zip(pts, pts[1:]):
        draw.line([a, b], fill=fill, width=width)
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def draw_arrowhead(draw, tip, direction, size, fill):
    import math
    dx, dy = direction
    ang = math.atan2(dy, dx)
    a1 = ang + math.radians(152)
    a2 = ang - math.radians(152)
    p1 = (tip[0] + size * math.cos(a1), tip[1] + size * math.sin(a1))
    p2 = (tip[0] + size * math.cos(a2), tip[1] + size * math.sin(a2))
    draw.polygon([tip, p1, p2], fill=fill)


def emblem(draw, cx, cy, r, scale=1.0):
    """沉积与回流徽记：圆环 + 三层沉积 + 回流箭头。"""
    ring_w = max(3, int(r * 0.06))
    # 沉积层（在圆内裁剪）——用蒙版画
    return ring_w


def draw_emblem(img, cx, cy, R):
    """在 img 上画完整徽记，R 为外圈半径。"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # 裁剪蒙版：内圆
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    inner = R * 0.965
    md.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=255)
    # 沉积层
    strata = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(strata)
    y0 = cy + R * 0.19
    sd.rectangle([cx - R, y0, cx + R, y0 + R * 0.155], fill=SAND + (235,))
    sd.rectangle([cx - R, y0 + R * 0.19, cx + R, y0 + R * 0.33], fill=STAY + (215,))
    sd.rectangle([cx - R, y0 + R * 0.37, cx + R, cy + R], fill=STAY_DEEP + (200,))
    layer.paste(strata, (0, 0), Image.composite(mask, Image.new("L", img.size, 0), mask))
    d = ImageDraw.Draw(layer)
    # 外圈（小尺寸下加重）
    small = R < 100
    ring_w = max(3, int(R * (0.075 if small else 0.045)))
    ring_col = (INK_SOFT if small else INK_FAINT) + (235,)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=ring_col, width=ring_w)
    # 虚线内圈
    import math
    r2 = R * 0.80
    n = 44
    for i in range(n):
        if i % 2:
            continue
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 0.85) / n
        d.arc([cx - r2, cy - r2, cx + r2, cy + r2],
              math.degrees(a0), math.degrees(a1), fill=INK_FAINT + (130,), width=max(2, ring_w // 2))
    # 回流曲线：从沉积层左侧向上、向右拱起
    s = R / 110.0
    p0 = (cx + (74 - 110) * s, cy + (131 - 110) * s)
    p1 = (cx + (70 - 110) * s, cy + (84 - 110) * s)
    p2 = (cx + (118 - 110) * s, cy + (54 - 110) * s)
    p3 = (cx + (148 - 110) * s, cy + (76 - 110) * s)
    pts = bezier(p0, p1, p2, p3)
    p4 = (cx + (170 - 110) * s, cy + (92 - 110) * s)
    p5 = (cx + (168 - 110) * s, cy + (116 - 110) * s)
    p6 = (cx + (152 - 110) * s, cy + (128 - 110) * s)
    pts += bezier(p3, p4, p5, p6)[1:]
    lw = max(4, int(R * (0.085 if small else 0.055)))
    draw_polyline(d, pts, RET + (255,), lw)
    dx = pts[-1][0] - pts[-3][0]
    dy = pts[-1][1] - pts[-3][1]
    draw_arrowhead(d, pts[-1], (dx, dy), lw * 3.1, RET + (255,))
    # 起点圆点
    dot_r = R * (0.10 if small else 0.075)
    d.ellipse([p0[0] - dot_r, p0[1] - dot_r, p0[0] + dot_r, p0[1] + dot_r], fill=STAY_DEEP + (255,))
    img.alpha_composite(layer)


def og_card():
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)

    # 底部沉积带
    d.rectangle([0, 500, W, 530], fill=SAND + (255,))
    d.rectangle([0, 534, W, 560], fill=STAY + (255,))
    d.rectangle([0, 564, W, H], fill=STAY_DEEP + (255,))
    for y in (500, 534, 564):
        d.line([0, y, W, y], fill=PAPER, width=3)

    # 右侧徽记
    draw_emblem(img, 985, 260, 150)
    d = ImageDraw.Draw(img)

    # 文本
    t_cn = load_font(SONGTI, 92, ("Songti SC Bold", "Bold"))
    t_en = load_font(MENLO, 26, ("Regular",))
    t_sub = load_font(SONGTI, 40, ("Songti SC Regular", "Regular"))
    t_kick = load_font(MENLO, 22, ("Regular",))

    x = 84
    # kicker
    kick = "INDEPENDENT RESEARCH PROGRAM · 2026"
    d.text((x + 2, 96), kick, font=t_kick, fill=STAY_DEEP)
    d.rounded_rectangle([x - 18, 84, x + d.textlength(kick, font=t_kick) + 20, 134],
                        radius=25, outline=STAY + (150,), width=2)

    d.text((x, 180), "选择性现实理论", font=t_cn, fill=INK)
    # 字距版英文
    ex, ey = x + 4, 306
    for ch in "SELECTIVE REALITY THEORY · SRT":
        d.text((ex, ey), ch, font=t_en, fill=INK_FAINT)
        ex += d.textlength(ch, font=t_en) + 6

    d.text((x, 372), "现实如何生成，秩序如何不封闭生成", font=t_sub, fill=INK_SOFT)

    img.convert("RGB").save(ASSETS / "og-card.png", optimize=True)
    print("og-card.png", img.size)


def touch_icon():
    S = 180
    img = Image.new("RGBA", (S, S), PAPER + (255,))
    draw_emblem(img, S / 2, S / 2, S * 0.42)
    img.convert("RGB").save(ASSETS / "apple-touch-icon.png", optimize=True)
    print("apple-touch-icon.png", img.size)


if __name__ == "__main__":
    og_card()
    touch_icon()
