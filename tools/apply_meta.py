#!/usr/bin/env python3
"""给全站页面注入/更新 head 元数据块（幂等，靠标记注释识别旧块）。

内容：meta description（每页手工调校）、canonical、favicon、theme-color、
Open Graph / Twitter 卡。og:image 用绝对 URL 指向 assets/og-card.png。
新增页面：在 DESC 里加一行描述后重跑 `python3 tools/apply_meta.py`。
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://zyx1st-png.github.io/srt-site/"
MARK_A = "<!-- meta:auto -->"
MARK_B = "<!-- /meta:auto -->"

DESC = {
    "index.html": "现实不是先被给定、再被选择；现实是在约束中的选择里变得确定。SRT 追问可能性如何变成现实，以及现实为什么会变硬、变厚、像是“一直如此”。",
    "corelaw.html": "七条论纲是 SRT 最短的一次自我陈述——整套理论压成七句的哲学宪章，附上它自己记录的未决张力：哪些还没推导完，就不许当已证的说。",
    "l0.html": "全站最底下的一层：四个命题的形而上学地基。所有上层的形式化、领域映射、实验设计都从这里出发，而不是反过来为它背书。",
    "direction.html": "SRT 最深的一次下注：断路比通路更贵。正面讲清这条最底层公设——它说什么、它不说什么、以及为什么标成“公设”而不藏进推导。",
    "suffering.html": "苦难的结构理论：它是什么的登记、分几型、为什么“把它压到最低”恰恰是错的。结构分析，不是临床诊断，不构成任何医疗建议。",
    "quantum.html": "把百年测量问题读成选择事件。全页是 P3 桥接翻译——不裁决哥本哈根与多世界之争，量子也不反过来充当 SRT 的证据。",
    "theory.html": "研究者路径入口：P0 原始公理与 P1 构成定理。每一条都同时给出它形式上说了什么，和它刻意不说什么。",
    "equations.html": "P0 公理给出语法，方程层给出可计算的动力学：动力学、热力学、稳定性主锚点方程摘选。",
    "operator.html": "选择算子 Ĝθ——SRT 里“谁在取值”的那台引擎。它不需要意识就能运转，却需要一个身体才能真正锚定。",
    "dynamics.html": "为什么选择动力学能跨尺度保持同构，以及选择在物理系统里留下什么可测的签名。",
    "l2.html": "选择留下痕迹，痕迹沉积成地形——这就是 L₂。同一片地形可以是地面也可以是牢笼，分野只有一条：后果还回不回得来。",
    "individuation.html": "“主语”从哪来？个体化不去证明主体存在，而是追踪：选择模式在什么结构条件下，会凝结出一个能持续承担自己选择的位置。",
    "collective.html": "许多主语共享同一片地形时，他们何时构成更高阶的选择单元，何时只是聚合，何时变成“有人选择、另一些人承受”。",
    "predictions.html": "一个理论若只会说“这个我也能解释”，就没有下注。这一页是 SRT 真正下注的地方：它在哪里预期与对手不同的结构，什么结果会削弱它。",
    "domains.html": "“排开 · 定形 · 写入”三步在物理、生物、社会、AI、意识里反复出现。横读看形式统一，竖读看机制差异；显影是显影，不是证据。",
    "domains/phys.html": "“排开 · 定形 · 写入”这三步在物理里长成什么样子，每条显影都标了它的主张硬度。",
    "domains/bio.html": "“排开 · 定形 · 写入”这三步在生物里长成什么样子，每条显影都标了它的主张硬度。",
    "domains/soc.html": "“排开 · 定形 · 写入”这三步在社会里长成什么样子，每条显影都标了它的主张硬度。",
    "domains/ai.html": "“排开 · 定形 · 写入”这三步在人工智能里长成什么样子，每条显影都标了它的主张硬度。",
    "domains/mind.html": "“排开 · 定形 · 写入”这三步在主体意识里长成什么样子，每条显影都标了它的主张硬度。",
    "consciousness.html": "SRT 不宣称“解决”意识的困难问题——它做的是消解与换问，并诚实标注哪些还没推导完；在此前提下给出感受质与意识门槛的结构立场。",
    "ai.html": "对 AI 的核心判断不是“它多聪明”，而是“后果回不回到它自己身上”。把“AI 有没有主体”从一句二元判决，换成两张可查的分级判据表。",
    "philosophy.html": "SRT 不宣布“解决了自由意志”“解决了意识”。它让老问题暴露出问得太晚、站得太窄，然后换一个更早的问题重新打开。",
    "spirituality.html": "SRT 不证明任何宗教为真，也不否证——它读出宗教与灵性语言在结构上做什么，尤其是它们如何内置反偶像化。",
    "comparison.html": "“这不就是 XX 吗？”——SRT 与七个最常被对照框架的分叉：X 抓住了重要的局部，SRT 追问它停下的地方。对照是定位，不是裁决。",
    "methodology.html": "SRT 给自己上的规矩：主张阶梯、冻结与编辑纪律、可证伪的下注规则、敌意评审。这部分和理论本身一样是作品。",
    "map.html": "全站理论地图：从最底层四命题往上长出稳定、主体与共同体，向外在各领域显影，再回头接受检验。每个节点都可点进去。",
    "visuals.html": "五张独立信息图解释 SRT 的层级、选择算子、本体论摩擦、主体个体化与 P0–P5 主张阶梯。",
    "book/index.html": "《从存在到秩序》——一部从 SRT 出发、但不被 SRT 封闭的生成哲学书。稳定不是起点，而是选择留下来的历史；秩序不是终点，而是后果回得来的地面。",
    "book/q05.html": "公开样章 · 第五章：你以为自己是从菜单里选了一道菜。但菜单是谁印的？“挑选”只是选择的最后一帧。",
    "articles.html": "《活的选择》系列：用 SRT 看清楚，再用不带术语的语言说出来。从日常经验进入，逐篇发布；理论本身不出现在文章里。",
    "value-hiddenness.html": "《活的选择》第一篇：价值不是缺席的，是被遮蔽的——从日常经验进入，不带术语地看清价值在哪里被挡住。",
    "video.html": "《从存在到秩序》视频序章 Q00：从一杯水、水平因果和沉积地形开始，追问在对象彼此相关之前，它们如何先成为‘它们’。含中文字幕试制版。",
    "videos.html": "《从存在到秩序》视频列表：按集查看 Q00 序章等视频的封面、时长和简介，进入独立详情页播放。",
    "papers.html": "SRT 论文与外部收录进度：Frontiers 论文已接收，Costly Selective Closure 已转投 Adaptive Behavior，意识图景获 LOC 收录。",
    "research.html": "SRT 当前研究进展：Frontiers 论文已接收，Costly Selective Closure 在投 Adaptive Behavior，意识图景获 LOC 收录。",
    "evidence.html": "SRT 证据与材料地图：区分收敛、代理、约束和验证，公开展示八张候选研究卡及其边界。当前尚无已接受的证据卡。",
    "articles/consciousness-before.html": "《意识之前》：SRT 对无意识智能、感受意识与反身意识的分层解释，一篇保留可错位置的条件性立场长文。",
    "en.html": "Selective Reality Theory (SRT) asks how possibilities become reality — and why reality hardens, thickens, and starts to look as if it had always been there.",
}

SKIP = {"404.html"}  # 自包含、noindex，不注入元数据块


def head_block(rel: str, title: str, desc: str, prefix: str, lang_en: bool) -> str:
    canonical = BASE + ("" if rel == "index.html" else rel)
    og_img = BASE + "assets/og-card.png"
    lines = [
        MARK_A,
        f'<meta name="description" content="{desc}"/>',
        f'<link rel="canonical" href="{canonical}"/>',
        f'<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"/>',
        f'<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png"/>',
        '<meta name="theme-color" content="#F6F3EB"/>',
        '<meta property="og:type" content="website"/>',
        '<meta property="og:site_name" content="选择性现实理论 · Selective Reality Theory"/>',
        f'<meta property="og:title" content="{title}"/>',
        f'<meta property="og:description" content="{desc}"/>',
        f'<meta property="og:url" content="{canonical}"/>',
        f'<meta property="og:image" content="{og_img}"/>',
        '<meta property="og:image:width" content="1200"/>',
        '<meta property="og:image:height" content="630"/>',
        f'<meta property="og:locale" content="{"en_US" if lang_en else "zh_CN"}"/>',
        '<meta name="twitter:card" content="summary_large_image"/>',
        MARK_B,
    ]
    return "\n".join(lines)


def main() -> int:
    missing = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP:
            continue
        if rel not in DESC:
            missing.append(rel)
            continue
        html = p.read_text(encoding="utf-8")
        title_m = re.search(r"<title>(.*?)</title>", html, re.S)
        title = title_m.group(1).strip() if title_m else "选择性现实理论"
        depth = rel.count("/")
        prefix = "../" * depth
        lang_en = 'lang="en"' in html.split(">", 2)[1] if ">" in html else False
        lang_en = bool(re.search(r'<html[^>]*lang="en"', html))
        block = head_block(rel, title, DESC[rel], prefix, lang_en)
        # 去掉旧块
        html = re.sub(re.escape(MARK_A) + r".*?" + re.escape(MARK_B) + r"\n?", "", html, flags=re.S)
        # 插到 </head> 前
        if "</head>" not in html:
            print(f"!! {rel}: 没有 </head>，跳过")
            continue
        html = html.replace("</head>", block + "\n</head>", 1)
        p.write_text(html, encoding="utf-8")
        print(f"ok {rel}")
    if missing:
        print("\n未配置 description（未处理）：")
        for m in missing:
            print(" -", m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
