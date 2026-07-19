#!/usr/bin/env python3
"""Static quality gate: links, metadata, stale claims, manifest boundaries."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json, re, sys
from sync_shared import nav as canonical_nav

ROOT = Path(__file__).resolve().parent.parent
VIDEO_CATALOG = json.loads((ROOT / "tools/video_catalog.json").read_text(encoding="utf-8"))["episodes"]
BANNED = ["理论主仓库私有维护", "书稿 · RC1 评审中", "五条 P0 原始公理", "序章 + 二十八章", "匿名评审中", "major revision 返修中"]
PUBLIC_BACKSTAGE = ["播放器不再加载", "避免重复显示", "直接烧录进视频画面", "字幕已烧录进画面", "播放器字幕轨道"]
REQUIRED_NAV_TARGETS = [
    "corelaw.html", "l0.html", "direction.html", "theory.html", "equations.html",
    "operator.html", "dynamics.html", "visuals.html", "map.html", "methodology.html", "l2.html",
    "individuation.html", "collective.html", "suffering.html", "predictions.html",
    "evidence.html", "research.html", "domains.html", "domains/library.html", "quantum.html",
    "consciousness.html", "ai.html", "philosophy.html", "spirituality.html",
    "comparison.html", "book/index.html", "book/q05.html", "articles.html",
    "articles/consciousness-before.html", "value-hiddenness.html", "videos.html",
    "papers.html",
] + [x["route"] for x in VIDEO_CATALOG if x["status"] == "published"]

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=[]; self.h1=0; self.lang=False; self.svg_depth=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag == "svg": self.svg_depth += 1
        if tag == "html": self.lang=bool(a.get("lang"))
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if a.get("id") and not self.svg_depth: self.ids.append(a["id"])
        if tag == "h1": self.h1 += 1
    def handle_endtag(self, tag):
        if tag == "svg" and self.svg_depth: self.svg_depth -= 1

def main():
    errors=[]; pages=[]
    for p in sorted(ROOT.rglob("*.html")):
        rel=p.relative_to(ROOT).as_posix(); text=p.read_text(encoding="utf-8"); parser=Page(); parser.feed(text)
        pages.append(rel)
        if rel != "404.html":
            for required in ['<meta name="description"', '<link rel="canonical"', '<meta property="og:title"']:
                if required not in text: errors.append(f"{rel}: missing {required}")
            if not parser.lang or parser.h1 != 1: errors.append(f"{rel}: lang/h1 invalid ({parser.h1})")
            nav = re.search(r'<!-- shared:nav -->(.*?)<!-- /shared:nav -->', text, re.S)
            if not nav:
                errors.append(f"{rel}: missing shared navigation")
            else:
                prefix = "../" * rel.count("/")
                if nav.group(0) != canonical_nav(prefix):
                    errors.append(f"{rel}: navigation drift from tools/sync_shared.py")
                for target in REQUIRED_NAV_TARGETS:
                    if not re.search(r'href="(?:\.\./)*' + re.escape(target) + r'"', nav.group(1)):
                        errors.append(f"{rel}: navigation missing {target}")
        if len(parser.ids) != len(set(parser.ids)): errors.append(f"{rel}: duplicate id")
        for phrase in BANNED:
            if phrase in text: errors.append(f"{rel}: stale phrase {phrase}")
        for phrase in PUBLIC_BACKSTAGE:
            if phrase in text: errors.append(f"{rel}: public backstage phrase leaked: {phrase}")
        for href in parser.links:
            u=urlsplit(href)
            if u.scheme or href.startswith(("#", "mailto:", "javascript:")): continue
            if u.path.startswith("/srt-site/"):
                target=(ROOT/unquote(u.path.removeprefix("/srt-site/"))).resolve()
            else:
                target=(p.parent/unquote(u.path)).resolve()
            if u.path.endswith("/"): target=target/"index.html"
            if not target.exists(): errors.append(f"{rel}: broken link {href}")
    manifest=json.loads((ROOT/"tools/content_manifest.json").read_text())
    forbidden=manifest["public_rules"]["forbidden_prefixes"]
    for entry in manifest["entries"]:
        if any(entry["source"].startswith(x) for x in forbidden): errors.append(f"manifest: forbidden source {entry['source']}")
        if not (ROOT/entry["target"]).exists(): errors.append(f"manifest: missing target {entry['target']}")
    evidence=(ROOT/"evidence.html").read_text(encoding="utf-8")
    if evidence.count("data-material-card") != 8: errors.append("evidence.html: expected 8 public material cards")
    if evidence.count('class="material-detail"') != 8: errors.append("evidence.html: expected 8 on-site material expansions")
    if "github.com/zyx1st-png/SRT-Pub/blob/" in evidence: errors.append("evidence.html: material card jumps directly to repository")
    if "尚无已接受的证据卡" not in evidence: errors.append("evidence.html: missing draft-evidence boundary")
    for backstage in ["Operations/", "Material Log", "A 类正文", "B 类延后", "C 类"]:
        if backstage in evidence: errors.append(f"evidence.html: backstage phrase leaked: {backstage}")
    papers=(ROOT/"papers.html").read_text(encoding="utf-8")
    for current_status in ["Frontiers in Neuroscience", "已接收", "Adaptive Behavior", "ALIFE 2026 未录用", "Landscape of Consciousness", "已收录"]:
        if current_status not in papers: errors.append(f"papers.html: missing current status {current_status}")
    visuals=(ROOT/"visuals.html").read_text(encoding="utf-8")
    infographic_assets=["srt-layers.webp", "selection-operator.webp", "payable-friction.webp", "individuation-thresholds.webp", "claim-ladder.webp"]
    for asset in infographic_assets:
        if asset not in visuals: errors.append(f"visuals.html: missing infographic {asset}")
        if not (ROOT/"assets/infographics"/asset).exists(): errors.append(f"visuals.html: missing asset file {asset}")
    if "图像是公众化转述，不是 canonical 定义源" not in visuals: errors.append("visuals.html: missing public-visual boundary")
    index=json.loads((ROOT/"assets/search-index.json").read_text())
    indexed={x["u"] for x in index}
    expected=set(pages)-{"404.html"}
    if indexed != expected: errors.append(f"search index drift: missing={sorted(expected-indexed)} extra={sorted(indexed-expected)}")
    videos=(ROOT/"videos.html").read_text(encoding="utf-8")
    for episode in VIDEO_CATALOG:
        if episode["status"] != "published": continue
        for key in ["route", "output", "poster"]:
            if not (ROOT/episode[key]).exists(): errors.append(f"video catalog: {episode['id']} missing {key} {episode[key]}")
        if episode["route"] not in videos: errors.append(f"videos.html: missing catalog episode {episode['id']}")
        if episode.get("subtitle"):
            from video_pipeline import audit_srt
            errors.extend(f"video catalog: {episode['id']} {e}" for e in audit_srt(
                ROOT/episode["subtitle"], strict=episode.get("quality_profile", "strict") == "strict"))
    if errors:
        print("\n".join(f"ERROR {e}" for e in errors)); return 1
    print(f"OK: {len(pages)} HTML pages, links/meta/claims/manifest/search index aligned")
    return 0

if __name__ == "__main__": sys.exit(main())
