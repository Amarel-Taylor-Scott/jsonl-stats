import io
import json
import os
import tempfile
import unittest

import jsonl_stats


SAMPLE_JSONL = """\
{"name": "alice", "age": 30, "tags": ["a", "b"]}
{"name": "bob", "age": 42, "active": true}
{"name": "carol", "active": false, "score": 9.5}
{"name": "dave", "age": null, "tags": ["c"]}
"""


class TestAnalyzeRecords(unittest.TestCase):
    def test_empty(self):
        stats = jsonl_stats.analyze_records([])
        self.assertEqual(stats["record_count"], 0)
        self.assertEqual(stats["key_frequency"], {})
        self.assertEqual(stats["type_histograms"], {})

    def test_sample(self):
        records = list(jsonl_stats.parse_jsonl(io.StringIO(SAMPLE_JSONL)))
        stats = jsonl_stats.analyze_records(records)

        self.assertEqual(stats["record_count"], 4)
        self.assertEqual(
            stats["key_frequency"],
            {"name": 4, "age": 3, "active": 2, "tags": 2, "score": 1},
        )
        self.assertEqual(
            stats["type_histograms"],
            {
                "name": {"str": 4},
                "age": {"int": 2, "null": 1},
                "tags": {"list": 2},
                "active": {"bool": 2},
                "score": {"float": 1},
            },
        )


class TestParseJsonl(unittest.TestCase):
    def test_skips_blank_lines(self):
        records = list(jsonl_stats.parse_jsonl(io.StringIO("\n\n{}\n\n{}\n")))
        self.assertEqual(len(records), 2)

    def test_rejects_non_object(self):
        with self.assertRaises(ValueError):
            list(jsonl_stats.parse_jsonl(io.StringIO("[1, 2, 3]\n")))

    def test_rejects_invalid_json(self):
        with self.assertRaises(json.JSONDecodeError):
            list(jsonl_stats.parse_jsonl(io.StringIO('{"bad\n')))


class TestFormatText(unittest.TestCase):
    def test_output_contains_sections(self):
        stats = jsonl_stats.analyze_records(list(jsonl_stats.parse_jsonl(io.StringIO(SAMPLE_JSONL))))
        text = jsonl_stats.format_text(stats)
        self.assertIn("record_count: 4", text)
        self.assertIn("key_frequency:", text)
        self.assertIn("type_histograms:", text)
        self.assertIn("name:", text)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.tmpdir.name, "input.jsonl")
        self.output_path = os.path.join(self.tmpdir.name, "output.txt")
        with open(self.input_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_JSONL)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_main_text_output(self):
        code = jsonl_stats.main([self.input_path, "-o", self.output_path])
        self.assertEqual(code, 0)
        with open(self.output_path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("record_count: 4", text)
        self.assertIn("age", text)

    def test_main_json_output(self):
        code = jsonl_stats.main([self.input_path, "--json", "-o", self.output_path])
        self.assertEqual(code, 0)
        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["record_count"], 4)
        self.assertEqual(data["key_frequency"]["name"], 4)

    def test_main_missing_file(self):
        code = jsonl_stats.main(["does_not_exist.jsonl"])
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
