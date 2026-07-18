#!/usr/bin/env python3
"""Import the publication-approved consciousness longread from SRT-Pub."""
from pathlib import Path
import re, subprocess

ROOT = Path(__file__).resolve().parent.parent
SOURCE_REPO = ROOT.parent / "SRT-Pub"
SOURCE = "Public_Content/SRT_Consciousness_Before_PUBLIC_LONGREAD_CN_2026-07-15.md"
TARGET = ROOT / "articles" / "consciousness-before.html"

def main() -> None:
    raw = subprocess.check_output(["git", "show", f"origin/main:{SOURCE}"], cwd=SOURCE_REPO, text=True)
    meta = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    if not meta or "publication_status: approved_for_publication" not in meta.group(1):
        raise SystemExit("source is not approved_for_publication")
    body = raw[meta.end():]
    rendered = subprocess.run(
        ["pandoc", "--from=gfm+tex_math_dollars", "--to=html5", "--wrap=none"],
        input=body, text=True, capture_output=True, check=True,
    ).stdout
    # The page hero owns the only h1.
    rendered = re.sub(r"<h1[^>]*>.*?</h1>", "", rendered, count=1, flags=re.S)
    rendered = rendered.replace("<h1", "<h2").replace("</h1>", "</h2>")
    html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>意识之前 · 选择性现实理论</title><link rel="stylesheet" href="../assets/style.css?v=20260718"/></head>
<body><div id="progress"></div><div class="topbar"><div class="wrap"><a class="brand brand-word" href="../index.html"><span>SRT</span><span class="brand-long">选择性现实理论</span></a><button class="navtoggle" aria-label="菜单" aria-expanded="false">菜单</button><nav class="topnav"></nav></div></div>
<header class="article-hero"><div class="wrap"><span class="kicker">公共立场长文 · 2026-07-17</span><h1>意识之前</h1><p class="en">SRT 对智能、感受与反身意识的分层解释</p><p class="lede">这不是“SRT 已经解决意识”的宣言，而是一个可受压、可反对、可修改的条件性立场。</p><div class="hero-meta"><span>公开审核通过</span><span>非 canonical</span><span>专业读者</span></div></div></header>
<main id="main"><article class="article-body">{rendered}</article><div class="article-end"><div class="source-note"><b>边界说明</b><p>本文是条件性立场文章，不是 SRT 的定义源。它区分无意识智能、感受意识和反身意识；对基质中立性、AI 主体性与意识消解均保留限定。</p></div><p><a class="btn ghost" href="../articles.html">返回文章列表</a></p></div></main>
<div class="guardrails"><div class="wrap"><span>智能不等于意识。</span><span>持久性不等于利害关切。</span><span>条件性解释不等于闭合证明。</span></div></div>
<footer><div class="wrap"><p>选择性现实理论 · 公共长文</p><p class="mark dim">站点内容为公众导览 · 定义与版本以 SRT-Pub 为准 · 2026-07-18 同步</p></div></footer><script src="../assets/site.js?v=20260718"></script></body></html>'''
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(html, encoding="utf-8")
    print(f"imported approved longread -> {TARGET.relative_to(ROOT)}")

if __name__ == "__main__": main()
