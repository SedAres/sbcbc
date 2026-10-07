import unittest

from library import cues_to_webvtt, natural_key, parse_subtitles


class SubtitleParserTests(unittest.TestCase):
    def test_srt_timestamps_and_safe_webvtt(self):
        source = """1
00:00:01,250 --> 00:00:03,500
Hello <script>alert(1)</script> & welcome.

2
00:00:04,000 --> 00:00:05,000
Second line
"""
        cues = parse_subtitles(source, ".srt")
        self.assertEqual(len(cues), 2)
        self.assertAlmostEqual(cues[0]["start"], 1.25)
        self.assertEqual(cues[1]["text"], "Second line")
        webvtt = cues_to_webvtt(cues)
        self.assertIn("WEBVTT", webvtt)
        self.assertIn("alert(1)", webvtt)
        self.assertIn("&amp;", webvtt)
        self.assertNotIn("<script>", webvtt)

    def test_vtt_with_cue_identifier_and_fractional_time(self):
        source = """WEBVTT

cue-a
00:00:00.100 --> 00:00:01.900 align:start
A caption
"""
        cues = parse_subtitles(source, ".vtt")
        self.assertEqual(cues, [{"start": 0.1, "end": 1.9, "text": "A caption"}])

    def test_ass_ssa_and_microdvd_are_supported(self):
        ass = r"Dialogue: 0,0:00:01.20,0:00:02.50,Default,,0,0,0,,First line\NSecond line"
        ass_cues = parse_subtitles(ass, ".ass")
        self.assertEqual(ass_cues[0]["text"], "First line\nSecond line")
        microdvd = "{25}{50}A frame-based caption"
        sub_cues = parse_subtitles(microdvd, ".sub")
        self.assertEqual(sub_cues[0]["start"], 1)
        self.assertEqual(sub_cues[0]["end"], 2)

    def test_natural_sort_does_not_compare_incompatible_types(self):
        self.assertEqual(sorted(["lesson10.mp4", "lesson2.mp4", "lesson1.mp4"], key=natural_key), [
            "lesson1.mp4", "lesson2.mp4", "lesson10.mp4"
        ])


if __name__ == "__main__":
    unittest.main()
