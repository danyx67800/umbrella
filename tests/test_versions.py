import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.data = json.loads(
            (ROOT / "versions.json").read_text(encoding="utf-8"))
        self.chromium = self.data["chromium"]
        self.header = (
            ROOT / "umbrella/common/umbrella_version.h").read_text(
                encoding="utf-8")

    def test_project_version_matches(self):
        self.assertEqual(self.version, self.data["version"])
        self.assertIn(f'kVersion = "{self.version}"', self.header)

    def test_chromium_tag_format(self):
        tag = self.chromium["tag"]
        self.assertRegex(tag, r"^\d+\.\d+\.\d+\.\d+$")
        self.assertTrue(tag.startswith(f"{self.chromium['milestone']}."))

    def test_chromium_commit_pinned(self):
        commit = self.chromium["commit"]
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertEqual(self.chromium["channel"], "stable")
        self.assertIn(f'kChromiumVersion = "{self.chromium["tag"]}"',
                      self.header)
        self.assertRegex(
            self.header,
            r'kChromiumCommit =\s+"' + re.escape(commit) + '"')

    def test_changelog_and_readme_reference_pin(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"[{self.version}]", changelog)
        self.assertIn(self.chromium["tag"], readme)
        self.assertIn(self.chromium["commit"], readme)

    def test_platform_is_windows_x64(self):
        self.assertIn("win-x64", self.data["platforms"])
        self.assertEqual(self.data["build"]["targetCpu"], "x64")
        self.assertFalse(self.data["build"]["isComponentBuild"])


if __name__ == "__main__":
    unittest.main()
