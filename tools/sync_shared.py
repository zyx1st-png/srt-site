#!/usr/bin/env python3
"""Synchronize the site's shared navigation and public status copy."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

GROUPS = [
    ("理解 SRT", True, [
        ("corelaw.html", "七条论纲"), ("l0.html", "L0 形而上学"),
        ("direction.html", "方向性 ε"), ("theory.html", "P0 / P1 核心"),
        ("equations.html", "四条主方程"), ("operator.html", "选择算子 Ĝθ"),
        ("dynamics.html", "动力学与尺度"), ("visuals.html", "概念图谱"), ("map.html", "全站理论地图"),
        ("methodology.html", "方法与治理"),
    ]),
    ("推导与检验", True, [
        ("l2.html", "L₂ 活／死稳定"), ("individuation.html", "个体化"),
        ("collective.html", "集体选择"), ("suffering.html", "苦难的结构"),
        ("predictions.html", "判别性预测"), ("evidence.html", "证据与材料"),
        ("research.html", "研究进展"),
    ]),
    ("领域与专题", True, [
        ("领域总览", [("domains.html", "跨域显影"), ("domains/library.html", "领域资料库")]),
        ("AI", [("ai.html", "AI 与主体门槛"), ("domains/library.html#ai", "架构／意识／本体 Annex")]),
        ("Neuroscience", [("consciousness.html", "意识与神经机制"), ("domains/library.html#neuroscience", "神经科学／接口 Annex")]),
        ("Physics", [("quantum.html", "量子测量"), ("domains/phys.html", "物理显影"), ("domains/library.html#physics", "量子／宇宙／QBox Annex")]),
        ("Philosophy", [("philosophy.html", "哲学延伸"), ("comparison.html", "理论对照"), ("domains/library.html#philosophy", "基础／伦理／政治 Annex")]),
        ("Spirituality", [("spirituality.html", "灵性与宗教语言"), ("domains/library.html#spirituality", "实践／传统／共同体")]),
    ]),
    ("内容与研究", True, [
        ("书稿", [("book/index.html", "《从存在到秩序》"), ("book/q05.html", "公开样章")]),
        ("文章", [("articles.html", "文章列表"), ("articles/consciousness-before.html", "《意识之前》"), ("value-hiddenness.html", "《价值不是缺席的》")]),
        ("视频", [("videos.html", "视频列表"), ("video.html", "Q00详情"), ("video-q01.html", "Q01详情")]),
        ("论文", [("papers.html", "论文集")]),
    ]),
]

STALE = {
    "2026-07-18 同步": "2026-07-19 同步",
    "synced 2026-07-18": "synced 2026-07-19",
    "站点内容为策展导出 · 理论主仓库私有维护 · 书稿 RC1-candidate 评审中":
        "站点内容为公众导览 · 定义与版本以 SRT-Pub 为准 · 2026-07-19 同步",
    "五条 P0 原始公理": "四条 P0 原始公理",
    "书稿 · RC1-candidate 评审中": "书稿 · 生成哲学战略总装",
    "序章 + 二十八章 · 五幕": "Q00–Q28 + 两章补章 · 五幕",
    "序章 + 二十八章": "Q00–Q28 + 两章补章",
    "RC1 冻结文本 · 原样呈现": "当前公开样章 · 2026-07 口径复核",
    "全书二十八章已成稿，正在进行 RC1 试读评审。": "当前主稿为 Q00–Q28，含两章补章与幕间桥段，正在进行生成哲学战略总装。",
    "私有维护": "在公开 SRT-Pub 主仓库维护",
    "Curated export · main repository maintained privately · book RC1-candidate under review": "Public guide · definitions and versions live in SRT-Pub · synced 2026-07-18",
    "Prologue plus twenty-eight chapters; RC1 under review. One sample chapter is public.": "The current manuscript spans Q00–Q28, two inserted chapters, and inter-act bridges. One sample chapter is public.",
    "序章加二十八章已成稿，RC1 冻结评审中。":
        "当前主稿为 Q00–Q28，含 Q04b、Q15b 与幕间桥段；五幕成立，正在进行生成哲学战略总装。",
}

def nav(prefix: str) -> str:
    chunks = []
    for label, wide, links in GROUPS:
        organized = links and isinstance(links[0][1], list)
        if organized:
            anchors = "".join(
                f'<div class="navgroup"><span class="navgroup-title">{group}</span>'
                + "".join(f'<a href="{prefix}{href}">{text}</a>' for href, text in group_links)
                + "</div>"
                for group, group_links in links
            )
        else:
            anchors = "".join(f'<a href="{prefix}{href}">{text}</a>' for href, text in links)
        panel_class = "navpanel navpanel-wide navpanel-organized" if organized else ("navpanel navpanel-wide" if wide else "navpanel")
        chunks.append(f'<div class="navitem"><span class="navlabel">{label}<i class="caret">▾</i></span><div class="{panel_class}">{anchors}</div></div>')
    chunks += [f'<a class="navlink" href="{prefix}en.html">EN</a>',
               f'<a class="navlink" href="{prefix}index.html#cta">联系</a>']
    return '<!-- shared:nav --><nav class="topnav">' + "".join(chunks) + '</nav><!-- /shared:nav -->'

def sync(check: bool = False) -> int:
    count = 0
    drift = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "404.html":
            continue
        html = path.read_text(encoding="utf-8")
        prefix = "../" * rel.count("/")
        canonical = nav(prefix)
        current = re.search(r'<!-- shared:nav -->.*?<!-- /shared:nav -->', html, re.S)
        if check:
            if not current:
                drift.append(f"{rel}: missing shared navigation")
            elif current.group(0) != canonical:
                drift.append(f"{rel}: navigation drift")
            count += 1
            continue
        html, n = re.subn(r'(?:<!-- shared:nav -->)?<nav class="topnav">.*?</nav>(?:<!-- /shared:nav -->)?', canonical, html, count=1, flags=re.S)
        if not n:
            raise SystemExit(f"missing nav: {rel}")
        for old, new in STALE.items():
            html = html.replace(old, new)
        if '<a class="skip-link"' not in html:
            html = html.replace('<body>', '<body>\n<a class="skip-link" href="#main">跳到正文</a>', 1)
        html = re.sub(r'<main(?![^>]*\bid=)', '<main id="main"', html, count=1)
        path.write_text(html, encoding="utf-8")
        count += 1
    if check:
        if drift:
            print("\n".join(f"DRIFT {item}" for item in drift))
            return 1
        print(f"shared navigation canonical: {count + len(drift)} pages")
        return 0
    print(f"shared navigation synchronized: {count} pages")
    return 0

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Synchronize or verify the canonical shared navigation.")
    parser.add_argument("--check", action="store_true", help="fail if any page differs from the canonical navigation")
    args = parser.parse_args()
    raise SystemExit(sync(check=args.check))

if __name__ == "__main__":
    main()
