#!/usr/bin/env python3
"""Repeatable SRT video pipeline: prepare, audit, render, publish, verify."""
from __future__ import annotations

import argparse
import html as html_lib
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools/video_catalog.json"
WORK = ROOT / "tools/video_work"
LIST_START = "<!-- generated:video-list -->"
LIST_END = "<!-- /generated:video-list -->"
SUSPICIOUS = {
    "舞会": "常见 balls 误译，应为球体或台球",
    "单元格": "生物语境通常应为细胞",
    "一代的连续运动": "generation 应按语境译为生成",
    "骑在他们的上面": "机器直译，应重写为附着其上",
    "预剪块": "机器直译，应重写为预先切好的方块/单元",
    "主要现实": "primary reality 应按语境译为首要现实",
}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))["episodes"]


def episode_map() -> dict[str, dict]:
    return {item["id"].upper(): item for item in load_catalog()}


def parse_time(value: str) -> int:
    h, m, rest = value.replace(".", ",").split(":")
    s, ms = rest.split(",")
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms.ljust(3, "0")[:3])


def parse_srt(path: Path) -> list[tuple[int, int, int, str]]:
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip()):
        lines = block.splitlines()
        if len(lines) < 3 or " --> " not in lines[1]:
            raise ValueError(f"invalid SRT block: {block[:80]!r}")
        start, end = lines[1].split(" --> ", 1)
        cues.append((int(lines[0]), parse_time(start), parse_time(end), " ".join(lines[2:]).strip()))
    return cues


def audit_srt(path: Path, strict: bool = True) -> list[str]:
    errors = []
    try:
        cues = parse_srt(path)
    except (ValueError, OSError) as exc:
        return [str(exc)]
    previous_end = -1
    for expected, (number, start, end, text) in enumerate(cues, 1):
        if number != expected:
            errors.append(f"cue {number}: expected sequence number {expected}")
        if start < previous_end:
            errors.append(f"cue {number}: overlaps previous cue by {previous_end - start} ms")
        if end <= start:
            errors.append(f"cue {number}: non-positive duration")
        if strict and end - start > 8000:
            errors.append(f"cue {number}: duration exceeds 8 seconds")
        if strict and len(text) > 30:
            errors.append(f"cue {number}: exceeds 30 Chinese characters")
        for phrase, reason in SUSPICIOUS.items():
            if phrase in text:
                errors.append(f"cue {number}: suspicious phrase {phrase!r} ({reason})")
        previous_end = end
    return errors


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tool_paths(args) -> tuple[Path, Path, Path]:
    pyvt = Path(args.pyvideotrans_root).expanduser().resolve()
    ffmpeg = pyvt / "ffmpeg/ffmpeg"
    ffprobe = pyvt / "ffmpeg/ffprobe"
    python = pyvt / ".venv/bin/python"
    for path in (ffmpeg, ffprobe, python):
        if not path.exists():
            raise SystemExit(f"missing pyvideotrans tool: {path}")
    return ffmpeg, ffprobe, python


def selected(args) -> list[dict]:
    mapping = episode_map()
    ids = [x.strip().upper() for x in args.episodes.split(",") if x.strip()]
    missing = [x for x in ids if x not in mapping]
    if missing:
        raise SystemExit(f"episodes missing from catalog: {', '.join(missing)}")
    return [mapping[x] for x in ids]


def prepare(args) -> None:
    _, _, python = tool_paths(args)
    source_dir = Path(args.source_dir).expanduser().resolve()
    for item in selected(args):
        source = source_dir / item["source_file"]
        target = WORK / item["id"]
        target.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            raise SystemExit(f"missing raw source: {source}")
        run([str(python), "-m", "whisper", str(source), "--model", args.model,
             "--language", args.language, "--task", "transcribe", "--output_format", "srt",
             "--output_dir", str(target), "--word_timestamps", "True", "--fp16", "False"])
        transcript = next(target.glob("*.srt"))
        brief = target / "REFINEMENT.md"
        brief.write_text(
            f"# {item['id']} {item['title']} 字幕精修门\n\n"
            f"原声转写：`{transcript.name}`\n\n"
            "必须结合当前书稿逐句精修，保留时间码；禁止逐词机翻。完成后把批准稿写入目录中的 "
            "`approved.zh.srt`，再运行 audit。\n\n"
            "检查重点：专名、SRT 术语、generation→生成、object file→对象档案、field→场；"
            "每条尽量不超过 20 个汉字，不允许时间重叠。\n",
            encoding="utf-8",
        )
        print(f"prepared {item['id']}: {transcript} + {brief}")


def render_one(args, item: dict) -> None:
    ffmpeg, ffprobe, _ = tool_paths(args)
    source_dir = Path(args.source_dir).expanduser().resolve()
    source = (source_dir / item["source_file"]).resolve()
    output = (ROOT / item["output"]).resolve()
    poster = (ROOT / item["poster"]).resolve()
    subtitle = (ROOT / item["subtitle"]).resolve() if item.get("subtitle") else None
    if item.get("subtitle_status") != "approved":
        raise SystemExit(f"{item['id']}: subtitle_status must be approved")
    if not source.exists():
        raise SystemExit(f"{item['id']}: raw source missing: {source}")
    source_error = validate_raw_source(source)
    if source_error:
        raise SystemExit(f"{item['id']}: {source_error}")
    if subtitle:
        errors = audit_srt(subtitle, strict=item.get("quality_profile", "strict") == "strict")
        if errors:
            raise SystemExit("\n".join(f"{item['id']}: {e}" for e in errors))
    probe = subprocess.run([str(ffprobe), "-v", "error", "-select_streams", "s",
                            "-show_entries", "stream=index", "-of", "csv=p=0", str(source)],
                           text=True, capture_output=True, check=True)
    if probe.stdout.strip():
        raise SystemExit(f"{item['id']}: raw source contains a subtitle stream; remove it before render")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.stem + ".building.mp4")
    vf = (f"subtitles=filename={subtitle}:fontsdir=/System/Library/Fonts:"
          "force_style='FontName=PingFang SC,FontSize=18,MarginV=18,Outline=1,Shadow=0'")
    run([str(ffmpeg), "-y", "-i", str(source), "-vf", vf, "-map", "0:v:0", "-map", "0:a:0?",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "copy",
         "-movflags", "+faststart", str(temporary)])
    temporary.replace(output)
    run([str(ffmpeg), "-y", "-ss", str(item.get("poster_second", 30)), "-i", str(source),
         "-frames:v", "1", "-q:v", "2", str(poster)])
    qa = WORK / item["id"] / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    for label, second in (("start", 15), ("middle", 150), ("end", 300)):
        run([str(ffmpeg), "-y", "-ss", str(second), "-i", str(output), "-frames:v", "1",
             str(qa / f"{label}.jpg")])
    record = {"episode": item["id"], "source_sha256": sha256(source),
              "subtitle_sha256": sha256(subtitle) if subtitle else None,
              "output_sha256": sha256(output), "source": str(source)}
    (WORK / item["id"] / "render.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"rendered {item['id']} from raw source only: {output}")


def video_list(items: list[dict]) -> str:
    cards = []
    for index, item in enumerate(items):
        current = " is-current" if index == 0 else ""
        cards.append(
            f'<article class="item{current}"><a class="poster" href="{item["route"]}" aria-label="打开 {item["id"]} 详情页">'
            f'<img src="{item["poster"]}" alt="{item["id"]} {item["title"]}视频封面"></a><div>'
            f'<span class="ep">{item["id"]} · {item["title"]}</span><h3>{item["question"]}</h3><p>{item["summary"]}</p></div>'
            f'<div class="meta"><span class="dur">{item["duration"]}</span><span class="chip ok">已上线</span>'
            f'<a class="watch" href="{item["route"]}">查看详情 →</a></div></article>'
        )
    return LIST_START + '<div class="clist video-list">' + "".join(cards) + '</div>' + LIST_END


def validate_raw_source(source: Path) -> str | None:
    source = source.resolve()
    if ROOT in source.parents:
        return "source must live outside the site repository"
    if source.name.endswith(("-zh.mp4", "-subtitled.mp4", "-fixed.mp4", "-polished.mp4")):
        return "source filename looks like a rendered output; use the original NotebookLM file"
    return None


def ensure_detail_page(item: dict) -> None:
    route = ROOT / item["route"]
    if route.exists():
        return
    template = (ROOT / "video-q02.html").read_text(encoding="utf-8")
    episode = html_lib.escape(item["id"])
    title = html_lib.escape(item["title"])
    question = html_lib.escape(item["question"])
    summary = html_lib.escape(item["summary"])
    description = html_lib.escape(item["description"])
    duration = html_lib.escape(item["duration"])
    route_name = html_lib.escape(item["route"])
    poster = html_lib.escape(item["poster"])
    output = html_lib.escape(item["output"])
    cue_count = len(parse_srt(ROOT / item["subtitle"])) if item.get("subtitle") else 0
    template = re.sub(r'<title>.*?</title>', f'<title>{episode} {title} · 视频详情 · 选择性现实理论</title>', template, count=1)
    template = re.sub(r'<meta name="description" content=".*?"/>', f'<meta name="description" content="{episode}《{title}》视频详情：{description} 中文字幕精修版。"/>', template, count=1)
    template = re.sub(r'<link rel="canonical" href=".*?"/>', f'<link rel="canonical" href="https://zyx1st-png.github.io/srt-site/{route_name}"/>', template, count=1)
    template = re.sub(r'<meta property="og:title" content=".*?"/>', f'<meta property="og:title" content="{episode} {title} · 视频详情 · 选择性现实理论"/>', template, count=1)
    template = re.sub(r'<meta property="og:description" content=".*?"/>', f'<meta property="og:description" content="{description}"/>', template, count=1)
    template = re.sub(r'<meta property="og:url" content=".*?"/>', f'<meta property="og:url" content="https://zyx1st-png.github.io/srt-site/{route_name}"/>', template, count=1)
    template = re.sub(r'<span class="kicker">.*?</span>', f'<span class="kicker">{episode} · Video detail</span>', template, count=1)
    template = re.sub(r'<h1>.*?</h1>', f'<h1>{question}</h1>', template, count=1)
    template = re.sub(r'(<header class="list-hero">.*?<h1>.*?</h1>)\s*<p>.*?</p>', rf'\1\n<p>{summary}</p>', template, count=1, flags=re.S)
    template = re.sub(r'<div class="cadence"><span class="pulse"></span>.*?</div>', f'<div class="cadence"><span class="pulse"></span>{episode} · {duration} · 中文字幕精修版</div>', template, count=1)
    player = (f'<div class="vhero"><video id="{episode.lower()}-player" controls preload="metadata" playsinline poster="{poster}" '
              f'aria-label="播放《从存在到秩序》{episode} {title}中文字幕精修版"><source src="{output}" type="video/mp4">'
              f'你的浏览器暂不支持网页视频，请<a href="{output}">直接打开视频</a>。</video>'
              f'<div class="vcap">{episode} · {title} · 中文字幕精修版 · {duration} · {cue_count} 条时间轴字幕</div></div>')
    template = re.sub(r'<div class="vhero">.*?</video><div class="vcap">.*?</div></div>', player, template, count=1, flags=re.S)
    note = (f'<div class="list-note video-page-note"><div class="callout">\n<b>本集简介</b>：{description}'
            '<br><br><b>字幕说明</b>：本集提供中文字幕精修版，时间轴与原声逐句校准。'
            '视频是面向公众的阐释，不是 SRT 的 canonical 定义源。\n</div></div>')
    template = re.sub(r'<div class="list-note video-page-note"><div class="callout">.*?</div></div>', note, template, count=1, flags=re.S)
    route.write_text(template, encoding="utf-8")
    print(f"created detail page: {route}")


def publish(args) -> None:
    items = [x for x in load_catalog() if x["status"] == "published"]
    for item in items:
        ensure_detail_page(item)
    page = ROOT / "videos.html"
    html = page.read_text(encoding="utf-8")
    if LIST_START not in html:
        html = re.sub(r'<div class="clist video-list">.*?</div>\s*(?=<div class="list-note)',
                      lambda _: video_list(items), html, count=1, flags=re.S)
    else:
        html = re.sub(re.escape(LIST_START) + r'.*?' + re.escape(LIST_END),
                      lambda _: video_list(items), html, count=1, flags=re.S)
    html = re.sub(r'<div class="cadence"><span class="pulse"></span>\d+ 部已上线',
                  f'<div class="cadence"><span class="pulse"></span>{len(items)} 部已上线', html, count=1)
    html = re.sub(r'<b>频道说明</b>：.*?(?=<br><br><b>发布状态</b>)',
                  '<b>频道说明</b>：这里展示已上线视频的封面、时长和简介；点击“查看详情”后进入独立播放页。\n',
                  html, count=1, flags=re.S)
    html = re.sub(r'<br><br><b>发布状态</b>：.*?(?=\n</div></div>)',
                  f'<br><br><b>发布状态</b>：当前 {len(items)} 集已上线；后续集数沿用同一列表—详情结构。',
                  html, count=1, flags=re.S)
    page.write_text(html, encoding="utf-8")
    run([sys.executable, str(ROOT / "tools/sync_shared.py")])
    run([sys.executable, str(ROOT / "tools/build_search_index.py")])
    run([sys.executable, str(ROOT / "tools/build_sitemap.py")])
    run([sys.executable, str(ROOT / "tools/check_site.py")])


def verify(_args) -> None:
    errors = []
    for item in load_catalog():
        if item["status"] != "published":
            continue
        for key in ("route", "output", "poster"):
            if not (ROOT / item[key]).exists():
                errors.append(f"{item['id']}: missing {key} {item[key]}")
        if item.get("subtitle"):
            errors.extend(f"{item['id']}: {e}" for e in audit_srt(
                ROOT / item["subtitle"], strict=item.get("quality_profile", "strict") == "strict"))
    if errors:
        raise SystemExit("\n".join(errors))
    print("video catalog, assets and subtitle timelines verified")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "audit", "render", "publish", "verify", "run"))
    parser.add_argument("--episodes", default="")
    parser.add_argument("--source-dir", default=str(Path.home() / "Downloads/SRT video"))
    parser.add_argument("--pyvideotrans-root", default=str(Path.home() / "Documents/其他/pyvideotrans"))
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="English")
    args = parser.parse_args()
    if args.command in {"prepare", "render", "run"} and not args.episodes:
        parser.error("--episodes is required")
    if args.command == "prepare": prepare(args)
    elif args.command == "audit": verify(args)
    elif args.command == "render":
        for item in selected(args): render_one(args, item)
    elif args.command == "publish": publish(args)
    elif args.command == "verify": verify(args)
    elif args.command == "run":
        for item in selected(args): render_one(args, item)
        publish(args)


if __name__ == "__main__":
    main()
