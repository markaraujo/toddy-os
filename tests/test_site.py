"""Prevent publishing private working files or broken relative source links."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import export_site


class PublicExport(unittest.TestCase):
    def test_only_allowlisted_files_are_exported(self):
        site = export_site.export(ROOT / "_site")
        actual = {str(p.relative_to(site)) for p in site.rglob("*") if p.is_file()}
        self.assertEqual(actual, {
            "index.html", ".nojekyll", "site.css",
            "ui/tokens.css", "ui/preview.css", "ui/preview.html", "ui/installer-slides.html",
            "assets/brand/toddy-os-system-icon.png",
            "assets/brand/toddy-os-wallpaper-dark.png", "assets/brand/toddy-os-wallpaper-light.png",
            "assets/brand/toddy-os-boot-background.png",
            "assets/brand/toddy-os-desktop-preview.png", "assets/brand/toddy-os-assistant-preview.png",
            "assets/brand/toddy-os-task-preview.png", "assets/brand/toddy-os-installer-preview.png",
        })
        content = (site / "index.html").read_text()
        self.assertNotIn('src="../', content)
        self.assertNotIn('href="../', content)
        self.assertNotIn("/home/", content)
        self.assertIn("https://github.com/markaraujo/toddy-os/blob/main/PRD.md", content)

    def test_export_refuses_checkout_or_other_destination(self):
        with self.assertRaises(ValueError):
            export_site.export(ROOT)


if __name__ == "__main__":
    unittest.main()
