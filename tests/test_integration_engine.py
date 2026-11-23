import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.engine import (  # noqa: E402
    GnListAdd,
    InsertAfter,
    RegexReplace,
    Replace,
    ReplaceFile,
    apply_operations,
)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.src = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, content):
        path = self.src / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        return path

    def read(self, relative):
        return (self.src / relative).read_text(encoding="utf-8")

    def apply(self, operations, check=False):
        return apply_operations(self.src, operations, check=check)

    def test_insert_after_then_idempotent(self):
        self.write("a.cc", '#include "a.h"\nint a;\n')
        operation = InsertAfter(
            file="a.cc", marker='#include "b.h"', description="test",
            anchor='#include "a.h"', text='\n#include "b.h"')
        first = self.apply([operation])
        self.assertEqual(first[0].status, "applied")
        self.assertIn('#include "a.h"\n#include "b.h"', self.read("a.cc"))

        second = self.apply([operation])
        self.assertEqual(second[0].status, "skipped")
        self.assertEqual(self.read("a.cc").count('#include "b.h"'), 1)

    def test_missing_anchor_fails(self):
        self.write("a.cc", "int a;\n")
        operation = InsertAfter(
            file="a.cc", marker="MARK", anchor="non esiste", text="x")
        result = self.apply([operation])[0]
        self.assertEqual(result.status, "error")
        self.assertIn("anchor trovato 0 volte", result.detail)

    def test_ambiguous_anchor_fails(self):
        self.write("a.cc", "x\nx\n")
        operation = InsertAfter(
            file="a.cc", marker="MARK", anchor="x", text="y")
        result = self.apply([operation])[0]
        self.assertEqual(result.status, "error")
        self.assertIn("2 volte", result.detail)

    def test_check_mode_never_writes(self):
        self.write("a.cc", "anchor\n")
        before = self.read("a.cc")
        operation = InsertAfter(
            file="a.cc", marker="MARK", anchor="anchor", text="\nmore")
        result = self.apply([operation], check=True)[0]
        self.assertEqual(result.status, "ok")
        self.assertEqual(self.read("a.cc"), before)

    def test_gn_list_add_and_duplicate(self):
        self.write(
            "BUILD.gn",
            'source_set("core") {\n'
            "  sources = [\n"
            '    "a.cc",\n'
            "  ]\n"
            "\n"
            "  deps = [\n"
            '    "//base",\n'
            "  ]\n"
            "}\n")
        operation = GnListAdd(
            file="BUILD.gn", marker='"b.cc"', description="test",
            target='source_set("core")', list_name="sources",
            value="b.cc")
        first = self.apply([operation])[0]
        self.assertEqual(first.status, "applied")
        text = self.read("BUILD.gn")
        self.assertIn('    "b.cc",', text)
        self.assertLess(text.index('"b.cc"'), text.index('"a.cc"'))

        second = self.apply([operation])[0]
        self.assertEqual(second.status, "skipped")
        self.assertEqual(text.count('"b.cc"'), 1)

    def test_gn_list_missing_target(self):
        self.write("BUILD.gn", 'source_set("other") {\n  deps = []\n}\n')
        operation = GnListAdd(
            file="BUILD.gn", marker='"x"', target='source_set("core")',
            list_name="deps", value="x")
        result = self.apply([operation])[0]
        self.assertEqual(result.status, "error")
        self.assertIn("trovato 0 volte", result.detail)

    def test_replace_and_regex(self):
        self.write("b.cc", "old\nName: Chromium\nName: Chromium\n")
        operations = [
            Replace(file="b.cc", marker="new", old="old", new="new"),
            RegexReplace(
                file="b.cc", marker="Name: Umbrella",
                pattern=r"Name: Chromium", replacement="Name: Umbrella",
                min_count=1, max_count=2),
        ]
        results = self.apply(operations)
        self.assertTrue(all(result.status == "applied" for result in results))
        text = self.read("b.cc")
        self.assertEqual(text.count("Name: Umbrella"), 2)

    def test_regex_count_out_of_range(self):
        self.write("b.cc", "Name: Chromium\n")
        operation = RegexReplace(
            file="b.cc", marker="Name: Umbrella",
            pattern=r"Name: Chromium", replacement="Name: Umbrella",
            min_count=2)
        result = self.apply([operation])[0]
        self.assertEqual(result.status, "error")

    def test_replace_file_hash_guard(self):
        content = "COMPANY=Old\n"
        self.write("BRANDING", content)
        good = hashlib.sha256(content.encode("utf-8")).hexdigest()
        operation = ReplaceFile(
            file="BRANDING", marker="PRODUCT=Umbrella", content="PRODUCT=Umbrella\n",
            expected_sha256=good)
        result = self.apply([operation])[0]
        self.assertEqual(result.status, "applied")
        self.assertEqual(self.read("BRANDING"), "PRODUCT=Umbrella\n")

        self.write("BRANDING", "COMPANY=Changed\n")
        operation2 = ReplaceFile(
            file="BRANDING", marker="PRODUCT=Umbrella", content="PRODUCT=Umbrella\n",
            expected_sha256=good)
        result2 = self.apply([operation2])[0]
        self.assertEqual(result2.status, "error")
        self.assertIn("sha256", result2.detail)

    def test_missing_file_is_error(self):
        operation = Replace(
            file="missing.cc", marker="x", old="a", new="b")
        result = self.apply([operation])[0]
        self.assertEqual(result.status, "error")
        self.assertIn("file non trovato", result.detail)


if __name__ == "__main__":
    unittest.main()
