#!/usr/bin/env python3
"""Synchronize the site's shared navigation and public status copy."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

GROUPS = [
    ("理解 SRT", [("corelaw.html", "七条论纲"), ("theory.html", "P0 / P1 核心"),
                  ("map.html", "理论地图"), ("methodology.html", "方法与治理")]),
    ("阅读", [("book/index.html", "《从存在到秩序》"), ("book/q05.html", "公开样章"),
                ("articles.html", "公共文章"), ("articles/consciousness-before.html", "意识之前")]),
    ("研究与证据", [("research.html", "研究进展"), ("evidence.html", "证据与未决问题"),
                    ("predictions.html", "可检验预测"), ("papers.html", "论文")]),
    ("主题", [("domains.html", "跨域显影"), ("consciousness.html", "意识"), ("ai.html", "AI"),
                ("philosophy.html", "哲学"), ("comparison.html", "理论对照")]),
]

STALE = {
    "站点内容为策展导出 · 理论主仓库私有维护 · 书稿 RC1-candidate 评审中":
        "站点内容为公众导览 · 定义与版本以 SRT-Pub 为准 · 2026-07-18 同步",
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
    for label, links in GROUPS:
        anchors = "".join(f'<a href="{prefix}{href}">{text}</a>' for href, text in links)
        chunks.append(f'<div class="navitem"><span class="navlabel">{label}<i class="caret">▾</i></span><div class="navpanel">{anchors}</div></div>')
    chunks += [f'<a class="navlink" href="{prefix}en.html">EN</a>',
               f'<a class="navlink" href="{prefix}index.html#cta">联系</a>']
    return '<!-- shared:nav --><nav class="topnav">' + "".join(chunks) + '</nav><!-- /shared:nav -->'

def main() -> None:
    count = 0
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "404.html":
            continue
        html = path.read_text(encoding="utf-8")
        prefix = "../" * rel.count("/")
        html, n = re.subn(r'(?:<!-- shared:nav -->)?<nav class="topnav">.*?</nav>(?:<!-- /shared:nav -->)?', nav(prefix), html, count=1, flags=re.S)
        if not n:
            raise SystemExit(f"missing nav: {rel}")
        for old, new in STALE.items():
            html = html.replace(old, new)
        if '<a class="skip-link"' not in html:
            html = html.replace('<body>', '<body>\n<a class="skip-link" href="#main">跳到正文</a>', 1)
        html = re.sub(r'<main(?![^>]*\bid=)', '<main id="main"', html, count=1)
        path.write_text(html, encoding="utf-8")
        count += 1
    print(f"shared navigation synchronized: {count} pages")

if __name__ == "__main__":
    main()
