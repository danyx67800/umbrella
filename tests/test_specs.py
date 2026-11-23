import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.engine import GnListAdd  # noqa: E402
from integration.specs import OPERATIONS  # noqa: E402

# Path GN (nel checkout) -> sorgente nel repository Umbrella.
SOURCE_MAP = {
    "umbrella/common/umbrella_prefs.cc":
        "umbrella/common/umbrella_prefs.cc",
    "umbrella/common/umbrella_version.cc":
        "umbrella/common/umbrella_version.cc",
    "umbrella/umbrella_browser_main_extra_parts.cc":
        "umbrella/browser/umbrella_browser_main_extra_parts.cc",
    "umbrella/umbrella_default_search.cc":
        "umbrella/browser/umbrella_default_search.cc",
    "umbrella/umbrella_new_tab_page.cc":
        "umbrella/browser/umbrella_new_tab_page.cc",
    "umbrella/ui/webui/umbrella_ui.cc":
        "umbrella/browser/ui/webui/umbrella_ui.cc",
}


class SpecTests(unittest.TestCase):
    def test_operation_count_is_meaningful(self):
        self.assertGreaterEqual(len(OPERATIONS), 20)

    def test_every_operation_has_description_and_marker(self):
        for operation in OPERATIONS:
            self.assertTrue(operation.description, operation.file)
            self.assertTrue(operation.marker, operation.file)

    def test_every_upstream_file_is_expected(self):
        allowed_prefixes = ("chrome/browser/", "chrome/app/")
        for operation in OPERATIONS:
            self.assertTrue(
                operation.file.startswith(allowed_prefixes),
                f"percorso inatteso: {operation.file}")

    def test_added_sources_exist_in_overlay(self):
        additions = [operation for operation in OPERATIONS
                     if isinstance(operation, GnListAdd)
                     and operation.list_name == "sources"]
        self.assertTrue(additions)
        for operation in additions:
            if not operation.value.endswith(".cc"):
                continue
            self.assertIn(operation.value, SOURCE_MAP,
                          f"mappatura mancante per {operation.value}")
            source = ROOT / SOURCE_MAP[operation.value]
            self.assertTrue(source.is_file(), f"sorgente assente: {source}")

    def test_webui_files_are_present(self):
        for relative in (
                "umbrella/browser/ui/webui/umbrella_ui.h",
                "umbrella/browser/ui/webui/umbrella_ui.cc",
                "umbrella/resources/index.html",
                "umbrella/resources/app.ts",
                "umbrella/resources/app.css",
                "umbrella/resources/BUILD.gn",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_no_duplicate_marker_per_file(self):
        seen = set()
        for operation in OPERATIONS:
            key = (operation.file, operation.marker)
            self.assertNotIn(key, seen, f"duplicato: {key}")
            seen.add(key)


if __name__ == "__main__":
    unittest.main()
