"""Prevent publishing private working files or broken relative source links."""
import importlib.util
import hashlib
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
        expected = {
            "assets/third-party/patreon/patreon-symbol.png", "assets/third-party/patreon/README.md",
            "index.html", ".nojekyll", "site.css",
            "ui/tokens.css", "ui/preview.css", "ui/preview.html", "ui/installer-slides.html",
            "ui/i18n.js", "ui/translations.js", "ui/mascot.js",
            "assets/brand/toddy-os-system-icon.png",
            "assets/brand/toddy-os-wallpaper-dark.png", "assets/brand/toddy-os-wallpaper-light.png",
            "assets/brand/toddy-os-boot-background.png",
            "assets/brand/toddy-os-wallpaper-dark-logo.png", "assets/brand/toddy-os-wallpaper-light-logo.png",
            "assets/brand/toddy-os-desktop-preview.png", "assets/brand/toddy-os-assistant-preview.png",
            "assets/brand/toddy-os-task-preview.png", "assets/brand/toddy-os-installer-preview.png",
            "assets/brand/web/toddy-yawn-half.png", "assets/brand/web/toddy-yawn-full.png",
        }
        expected.update("assets/third-party/gnome/" + name for name in ('ADWAITA-COPYRIGHT.txt', 'CONSOLE-COPYING.txt', 'EPIPHANY-COPYING.txt', 'GPL-2', 'GPL-3', 'NAUTILUS-COPYRIGHT.txt', 'README.md', 'SETTINGS-COPYRIGHT.txt', 'audio-input-microphone-symbolic.svg', 'audio-volume-high-symbolic.svg', 'document-open-recent-symbolic.svg', 'edit-find-symbolic.svg', 'folder-documents-symbolic.svg', 'folder-documents.svg', 'folder-download-symbolic.svg', 'folder-download.svg', 'folder-music.svg', 'folder-pictures-symbolic.svg', 'folder-pictures.svg', 'folder-templates.svg', 'folder.svg', 'go-next-symbolic.svg', 'go-previous-symbolic.svg', 'manifest.json', 'media-playback-stop-symbolic.svg', 'network-wireless-signal-excellent-symbolic.svg', 'open-menu-symbolic.svg', 'org.gnome.Console.svg', 'org.gnome.Epiphany.svg', 'org.gnome.Nautilus.svg', 'org.gnome.Settings.svg', 'starred-symbolic.svg', 'system-shutdown-symbolic.svg', 'user-home-symbolic.svg', 'user-trash-symbolic.svg', 'view-app-grid-symbolic.svg', 'window-close-symbolic.svg'))
        self.assertEqual(actual, expected)
        content = (site / "index.html").read_text()
        self.assertNotIn('src="../', content)
        self.assertNotIn('href="../', content)
        self.assertNotIn("/home/", content)
        self.assertIn("https://github.com/markaraujo/toddy-os/blob/main/PRD.md", content)
        # The HTML must request the CSS corresponding to this exact deployment.
        digest = hashlib.sha256((ROOT / "dashboard/site.css").read_bytes()).hexdigest()[:12]
        self.assertIn(f'href="site.css?v={digest}"', content)
        self.assertIn('href="https://www.patreon.com/ToddyOS"', content)
        self.assertIn('src="assets/third-party/patreon/patreon-symbol.png"', content)
        self.assertNotIn('href="https://www.paypal.com/donate', content)

    def test_export_refuses_checkout_or_other_destination(self):
        with self.assertRaises(ValueError):
            export_site.export(ROOT)


if __name__ == "__main__":
    unittest.main()
