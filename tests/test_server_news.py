import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scripts.generate.generate_server_news import (
    NEWS_ID, ask_news_settings, generate_server_news,
)


class ServerNewsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "list.json"
        self.existing = {"News": [
            {"NewsId": "news-" + str(i), "Title": "Original", "Content": "Original",
             "StartAt": 100, "EndAt": 1000, "IsNew": False, "Status": i % 2}
            for i in range(5)
        ], "Other": {"preserve": True}}
        self.path.write_text(json.dumps(self.existing), encoding="utf-8")
        self.date = datetime.datetime(2026, 10, 2, tzinfo=datetime.timezone.utc)

    def generate(self, **settings):
        generate_server_news(settings, self.path, self.date)
        return json.loads(self.path.read_text(encoding="utf-8"))

    def test_preserves_every_existing_entry_and_schema(self):
        data = self.generate(title="My server", content="Welcome!")
        self.assertEqual(data["News"][1:], self.existing["News"])
        self.assertEqual(data["Other"], self.existing["Other"])
        notice = data["News"][0]
        self.assertEqual(set(notice), set(self.existing["News"][0]))
        for key in notice:
            self.assertIs(type(notice[key]), type(self.existing["News"][0][key]))
        self.assertEqual(notice["NewsId"], NEWS_ID)
        self.assertEqual(notice["StartAt"], int(self.date.timestamp()))
        self.assertEqual(notice["EndAt"] - notice["StartAt"], 900)

    def test_rerun_replaces_only_generated_entry(self):
        self.generate(title="First")
        data = self.generate(title="Second")
        self.assertEqual(len(data["News"]), 6)
        self.assertEqual(data["News"][0]["Title"], "Second")
        self.assertEqual(data["News"][1:], self.existing["News"])

    def test_empty_news_list_can_receive_notice(self):
        self.path.write_text('{"News": []}', encoding="utf-8")
        data = self.generate(title="Welcome")
        self.assertEqual(len(data["News"]), 1)
        self.assertEqual(data["News"][0]["Title"], "Welcome")
        self.assertEqual(set(data["News"][0]), set(self.existing["News"][0]))

    def test_disabled_leaves_exact_file_unchanged(self):
        self.generate(title="Existing setup notice")
        before = self.path.read_bytes()
        self.generate(enabled=False)
        self.assertEqual(self.path.read_bytes(), before)

    def test_operator_text_is_escaped_and_line_breaks_supported(self):
        data = self.generate(title="Name", content="<script>x</script> & hello\nNext line")
        self.assertEqual(data["News"][0]["Content"],
                         "&lt;script&gt;x&lt;/script&gt; &amp; hello<br>Next line")

    def test_environment_inputs_are_noninteractive(self):
        with patch.dict(os.environ, {"EMBLEO_NEWS_TITLE": "Build 123",
                                    "EMBLEO_NEWS_CONTENT": "Public deployment details",
                                    "ASSET_SERVER_URL": "private-asset-url"}, clear=True):
            generate_server_news(path=self.path, now=self.date)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["News"][0]["Title"], "Build 123")
        self.assertNotIn("private-asset-url", self.path.read_text(encoding="utf-8"))

    def test_optional_prompts_and_defaults(self):
        with patch.dict(os.environ, {}, clear=True), patch("builtins.input", side_effect=["", "", ""]):
            settings = ask_news_settings()
        self.assertEqual(settings, {"enabled": True, "title": "Embleo Server",
                                    "content": "Welcome to Tales of Luminaria."})
        with patch.dict(os.environ, {}, clear=True), patch("builtins.input", return_value="n") as prompt:
            settings = ask_news_settings()
        self.assertFalse(settings["enabled"])
        self.assertEqual(prompt.call_count, 1)


if __name__ == "__main__":
    unittest.main()
