import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESOURCES = ROOT / "umbrella" / "resources"


def kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.tokens = json.loads(
            (ROOT / "design/tokens.json").read_text(encoding="utf-8"))
        self.html = (RESOURCES / "index.html").read_text(encoding="utf-8")
        self.css = (RESOURCES / "app.css").read_text(encoding="utf-8")
        self.ts = (RESOURCES / "app.ts").read_text(encoding="utf-8")
        self.build = (RESOURCES / "BUILD.gn").read_text(encoding="utf-8")
        self.ui = (ROOT / "umbrella/browser/ui/webui/umbrella_ui.cc").read_text(
            encoding="utf-8")

    def test_all_color_tokens_present_in_css(self):
        for theme in ("dark", "light"):
            for name, value in self.tokens["color"][theme].items():
                variable = f"--um-{kebab(name)}:"
                self.assertIn(variable, self.css)
                self.assertIn(value.lower(), self.css.lower(),
                              f"{theme}.{name} assente dal CSS")

    def test_radius_and_motion_tokens_present(self):
        for value in self.tokens["radius"].values():
            self.assertIn(value, self.css)
        for key in ("fast", "base", "slow"):
            self.assertIn(self.tokens["motion"][key], self.css)

    def test_no_remote_content_or_frames(self):
        self.assertNotIn("<iframe", self.html.lower())
        self.assertNotIn("http://", self.html)
        self.assertNotIn("http://", self.css)
        self.assertNotIn("http://", self.ts)
        self.assertNotIn("url(http", self.css)

    def test_csp_is_restrictive(self):
        csp = self.html[self.html.index("Content-Security-Policy"):]
        csp = csp[:csp.index(">")]
        self.assertIn("frame-src 'none'", csp)
        self.assertIn("connect-src 'none'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("script-src 'self'", csp)

    def test_no_inline_scripts(self):
        inline = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", self.html)
        self.assertEqual(inline, [])
        self.assertIn('src="app.js"', self.html)

    def test_search_uses_duckduckgo_with_encoding(self):
        self.assertIn("https://duckduckgo.com/?q=", self.ts)
        self.assertIn("encodeURIComponent(value)", self.ts)
        self.assertNotIn("google.com/search", self.ts)

    def test_no_network_apis_in_page(self):
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket"):
            self.assertNotIn(forbidden, self.ts)

    def test_shortcuts_are_editable_and_reorderable(self):
        for token in ("draggable = true", "openShortcutDialog",
                      "moveShortcut", "localStorage"):
            self.assertIn(token, self.ts)

    def test_accessibility_hooks(self):
        self.assertIn('aria-label', self.html)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn(":focus-visible", self.css)

    def test_build_webui_configuration(self):
        self.assertIn("build_webui", self.build)
        self.assertIn('grd_prefix = "umbrella"', self.build)
        self.assertIn("app.ts", self.build)
        self.assertIn('webui_context_type = "trusted"', self.build)

    def test_grit_resource_ids_match_files(self):
        # app.js è generato da build_webui a partire da app.ts.
        expected = {
            "IDR_UMBRELLA_INDEX_HTML": "index.html",
            "IDR_UMBRELLA_APP_CSS": "app.css",
            "IDR_UMBRELLA_APP_JS": "app.ts",
            "IDR_UMBRELLA_UMBRELLA_MARK_SVG": "umbrella-mark.svg",
        }
        for resource_id, filename in expected.items():
            self.assertIn(resource_id, self.ui)
            self.assertTrue((RESOURCES / filename).is_file(), filename)

    def test_grit_header_matches_build_webui_output(self):
        # build_webui genera l'header in chrome/grit/, non sotto resources/.
        self.assertIn('#include "chrome/grit/umbrella_resources.h"', self.ui)

    def test_private_mode_strings_not_claimed(self):
        combined = (self.html + self.css + self.ts).lower()
        self.assertNotIn("telemetry", combined)
        self.assertNotIn("adblock", combined)


if __name__ == "__main__":
    unittest.main()
