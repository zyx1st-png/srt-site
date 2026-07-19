#!/usr/bin/env python3
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from video_pipeline import ROOT, audit_srt, validate_raw_source


class VideoPipelineTests(unittest.TestCase):
    def make_srt(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return Path(handle.name)

    def test_clean_timeline(self):
        path = self.make_srt("1\n00:00:00,000 --> 00:00:01,000\n现实不是预切好的方块。\n\n2\n00:00:01,000 --> 00:00:02,000\n对象是生成的结果。\n")
        self.assertEqual(audit_srt(path), [])

    def test_overlap_is_blocking(self):
        path = self.make_srt("1\n00:00:00,000 --> 00:00:02,000\n第一条\n\n2\n00:00:01,900 --> 00:00:03,000\n第二条\n")
        self.assertTrue(any("overlaps" in item for item in audit_srt(path)))

    def test_machine_translation_phrase_is_blocking(self):
        path = self.make_srt("1\n00:00:00,000 --> 00:00:01,000\n舞会是现实的基础。\n")
        self.assertTrue(any("舞会" in item for item in audit_srt(path)))

    def test_rendered_file_cannot_be_source(self):
        self.assertIsNotNone(validate_raw_source(Path("/tmp/Q03-zh.mp4")))
        self.assertIsNotNone(validate_raw_source(ROOT / "assets/media/q03.mp4"))
        self.assertIsNone(validate_raw_source(Path.home() / "Downloads/SRT video/Q03_前对象场.mp4"))


if __name__ == "__main__":
    unittest.main()
