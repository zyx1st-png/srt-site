#!/usr/bin/env python3
"""生成 sitemap.xml。lastmod 取各文件最近一次 git 提交日期；新增页面后重跑。"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://zyx1st-png.github.io/srt-site/"
SKIP = {"404.html"}


def lastmod(p: pathlib.Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(p.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return out
    except subprocess.CalledProcessError:
        pass
    import datetime
    return datetime.date.today().isoformat()


def main() -> None:
    urls = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP:
            continue
        loc = BASE + ("" if rel == "index.html" else rel)
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod(p)}</lastmod></url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"sitemap.xml: {len(urls)} urls")


if __name__ == "__main__":
    main()
