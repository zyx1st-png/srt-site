#!/usr/bin/env python3
"""Create a reviewable Chinese subtitle draft from a Whisper SRT transcript.

This tool intentionally leaves the catalog in ``draft`` status. A draft must
pass the term/length audit and a human semantic review before it is approved
for rendering.
"""
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator

from video_pipeline import ROOT, audit_srt, parse_srt


TERM_REPLACEMENTS = {
    "选择": "选择",
    "排除": "排除",
    "塑形": "定形",
    "写入": "写入",
    "前对象场": "前对象场",
    "对象化": "对象化",
    "给定性": "给定性",
    "生成": "生成",
    "沉积": "沉积",
    "锚定": "锚定",
    "关切": "关切",
    "能动性": "能动性",
    "脚手架": "脚手架",
    "牢笼": "牢笼",
}


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    for source, replacement in TERM_REPLACEMENTS.items():
        text = text.replace(source, replacement)
    return text.replace(" ,", "，").replace(" .", "。")


def compact(text: str, limit: int = 30) -> str:
    """Keep a cue displayable; the source timing remains unchanged."""
    if len(text) <= limit:
        return text
    clauses = re.split(r"([，。；：、])", text)
    chosen = ""
    for index in range(0, len(clauses), 2):
        candidate = chosen + clauses[index] + (clauses[index + 1] if index + 1 < len(clauses) else "")
        if len(candidate) > limit:
            break
        chosen = candidate
    return chosen.rstrip("，；：、") or text[:limit]


def timestamp(ms: int) -> str:
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    seconds, ms = divmod(ms, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    translator = GoogleTranslator(source="en", target="zh-CN")
    cues = parse_srt(args.input)
    blocks = []
    for number, start, end, source in cues:
        for attempt in range(3):
            try:
                translated = clean(translator.translate(source))
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))
        blocks.append(f"{number}\n{timestamp(start)} --> {timestamp(end)}\n{compact(translated)}")
        time.sleep(0.08)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    errors = audit_srt(args.output)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"draft written: {args.output} ({len(cues)} cues)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
