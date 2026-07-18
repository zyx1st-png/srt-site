#!/usr/bin/env python3
"""构建全站搜索索引 assets/search-index.json。

每页一条记录：u=相对路径，t=短标题，d=meta description，x=正文纯文本。
页面内容改动后重跑：python3 tools/build_search_index.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "search-index.json"
SKIP = {"404.html"}
SITE_SUFFIX = re.compile(r"\s*·\s*(选择性现实理论|从存在到秩序|Selective Reality Theory)\s*$")


def page_text(html: str) -> str:
    # 去导航/页脚/脚本/SVG，留 hero + main
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    html = re.sub(r"<svg.*?</svg>", " ", html, flags=re.S)
    html = re.sub(r'<div class="topbar".*?</nav>(?:<!-- /shared:nav -->)?</div></div>', " ", html, flags=re.S)
    html = re.sub(r'<div class="guardrails">.*?</div></div>', " ", html, flags=re.S)
    html = re.sub(r"<footer.*?</footer>", " ", html, flags=re.S)
    body = re.search(r"<body.*?</body>", html, flags=re.S)
    text = body.group(0) if body else html
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> None:
    records = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP:
            continue
        html = p.read_text(encoding="utf-8")
        title_m = re.search(r"<title>(.*?)</title>", html, re.S)
        title = SITE_SUFFIX.sub("", title_m.group(1).strip()) if title_m else rel
        desc_m = re.search(r'<meta name="description" content="([^"]*)"', html)
        desc = desc_m.group(1) if desc_m else ""
        records.append({"u": rel, "t": title, "d": desc, "x": page_text(html)})
    OUT.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    total = sum(len(r["x"]) for r in records)
    print(f"{len(records)} pages, {total} chars -> {OUT.name} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
