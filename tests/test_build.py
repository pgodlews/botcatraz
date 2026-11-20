"""Builds the pages from the sample data and checks what comes out.

    python3 -m unittest discover -s tests
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"/\*__[A-Z]+__\*/|\{\{[A-Z]+\}\}|<!--NAV-->")


class SampleBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.www = Path(cls.tmp.name) / "www"
        subprocess.run([sys.executable, str(ROOT / "build.py"), "--sample", "--www", str(cls.www)],
                       check=True, cwd=ROOT, capture_output=True, text=True)
        cls.pages = sorted(cls.www.rglob("*.html"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_files(self):
        names = {str(p.relative_to(self.www)) for p in self.www.rglob("*") if p.is_file()}
        for sid in ("sample1", "sample2"):
            for name in ("index.html", "yard.html", "yard.json"):
                self.assertIn(f"{sid}/{name}", names)
        self.assertIn("index.html", names)

    def test_no_placeholders_left(self):
        for page in self.pages:
            left = PLACEHOLDER.findall(page.read_text())
            self.assertEqual(left, [], page.relative_to(self.www))

    def test_robot_types_and_mugshots_agree(self):
        art = ROOT / "yard" / "art"
        sheets = len(list((art / "robots").glob("robot-*.png")))
        robots = json.loads((art / "robots" / "robots.json").read_text())["variants"]
        mugs = json.loads((art / "mugshots" / "mugshots.json").read_text())["variants"]
        self.assertEqual(len([v for v in robots if v["file"].startswith("robot-")]), sheets)
        self.assertEqual(len(mugs), sheets)
        for v in mugs:
            self.assertTrue((art / "mugshots" / v["front"]).exists(), v["front"])
            self.assertTrue((art / "mugshots" / v["side"]).exists(), v["side"])

    def test_scripts_parse(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        script = re.compile(r"<script>(.*?)</script>", re.S)
        with tempfile.TemporaryDirectory() as tmp:
            for page in self.pages:
                for n, body in enumerate(script.findall(page.read_text())):
                    path = Path(tmp) / f"{page.parent.name}-{page.stem}-{n}.js"
                    path.write_text(body)
                    done = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
                    self.assertEqual(done.returncode, 0, f"{page.relative_to(self.www)}: {done.stderr}")


if __name__ == "__main__":
    unittest.main()
