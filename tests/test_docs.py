import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "docs/ARCHITECTURE.md",
    "docs/BUILD.md",
    "docs/PATCHES.md",
    "docs/ROADMAP.md",
    "docs/SECURITY.md",
    "docs/DESIGN.md",
    "docs/TESTING.md",
    "docs/RELEASING.md",
    "patches/README.md",
]


class DocsTests(unittest.TestCase):
    def test_required_documents_exist(self):
        for relative in REQUIRED:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(len(path.read_text(encoding="utf-8")), 200,
                               relative)

    def test_readme_links_resolve(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#]+)\)", readme):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            self.assertTrue((ROOT / target).exists(), target)

    def test_no_unverified_claims(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        # La build non è stata eseguita: il README deve dichiararlo.
        self.assertIn("non compilato", readme.lower())
        self.assertIn("bloccata", readme.lower())

    def test_security_documents_network_services(self):
        security = (ROOT / "docs/SECURITY.md").read_text(encoding="utf-8")
        for service in ("Safe Browsing", "Component updater", "Variations",
                        "DNS/HTTPS probing"):
            self.assertIn(service, security)


if __name__ == "__main__":
    unittest.main()
