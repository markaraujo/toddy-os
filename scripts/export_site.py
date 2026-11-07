#!/usr/bin/env python3
"""Export an explicit public page/design allowlist; never publish the checkout."""
import argparse
import hashlib
import json
import posixpath
import re
import shutil
from pathlib import Path

import project

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/markaraujo/toddy-os/blob/main/"
BRAND_FILES = (
    "toddy-os-system-icon.png", "toddy-os-wallpaper-dark.png",
    "toddy-os-wallpaper-light.png", "toddy-os-boot-background.png",
    "toddy-os-wallpaper-dark-logo.png", "toddy-os-wallpaper-light-logo.png",
    "toddy-os-desktop-preview.png", "toddy-os-assistant-preview.png",
    "toddy-os-task-preview.png", "toddy-os-installer-preview.png",
    "web/toddy-yawn-half.png", "web/toddy-yawn-full.png", "web/toddy-happy.png",
)
UI_FILES = ("tokens.css", "preview.css", "preview.html", "installer-slides.html", "i18n.js", "translations.js", "mascot.js", "supporters.js", "supporter-thanks.js")

ICON_FILES = ('ADWAITA-COPYRIGHT.txt', 'CONSOLE-COPYING.txt', 'EPIPHANY-COPYING.txt', 'GPL-2', 'GPL-3', 'NAUTILUS-COPYRIGHT.txt', 'README.md', 'SETTINGS-COPYRIGHT.txt', 'audio-input-microphone-symbolic.svg', 'audio-volume-high-symbolic.svg', 'document-open-recent-symbolic.svg', 'edit-find-symbolic.svg', 'folder-documents-symbolic.svg', 'folder-documents.svg', 'folder-download-symbolic.svg', 'folder-download.svg', 'folder-music.svg', 'folder-pictures-symbolic.svg', 'folder-pictures.svg', 'folder-templates.svg', 'folder.svg', 'go-next-symbolic.svg', 'go-previous-symbolic.svg', 'manifest.json', 'media-playback-stop-symbolic.svg', 'network-wireless-signal-excellent-symbolic.svg', 'open-menu-symbolic.svg', 'org.gnome.Console.svg', 'org.gnome.Epiphany.svg', 'org.gnome.Nautilus.svg', 'org.gnome.Settings.svg', 'starred-symbolic.svg', 'system-shutdown-symbolic.svg', 'user-home-symbolic.svg', 'user-trash-symbolic.svg', 'view-app-grid-symbolic.svg', 'window-close-symbolic.svg')


def public_links(content):
    """Keep design pages on Pages, and route repository documentation to GitHub."""
    content = content.replace('src="../assets/', 'src="assets/')
    content = content.replace('src="../ui/', 'src="ui/')
    content = content.replace('href="../ui/', 'href="ui/')
    content = content.replace('href="../assets/', 'href="assets/')
    return content.replace('href="../', f'href="{REPO_URL}')


def version_resources(content, relative, sources):
    """Keep a refreshed page from reusing incompatible cached CSS or JavaScript."""
    def replace(match):
        attribute, url = match.groups()
        key = posixpath.normpath(posixpath.join(posixpath.dirname(relative), url))
        source = sources.get(key)
        if source is None:
            return match.group(0)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        return f'{attribute}="{url}?v={digest}"'
    return re.sub(r'(href|src)="([^"?]+\.(?:css|js))"', replace, content)


def export(destination):
    destination = destination.resolve()
    if destination != ROOT / "_site":
        raise ValueError("Export destination must be the project's generated _site directory")
    data = json.loads((ROOT / "status.json").read_text())
    project.validate(data)
    page = public_links(project.outputs(data)["dashboard/index.html"])
    # Validate every source before replacing the previous generated export.
    sources = {"site.css": ROOT / "dashboard/site.css", "supporters.css": ROOT / "dashboard/supporters.css"}
    sources.update({f"assets/brand/{name}": ROOT / "assets/brand" / name for name in BRAND_FILES})
    sources.update({f"ui/{name}": ROOT / "ui" / name for name in UI_FILES})
    sources.update({f"assets/third-party/gnome/{name}": ROOT / "assets/third-party/gnome" / name for name in ICON_FILES})
    sources.update({f"assets/third-party/patreon/{name}": ROOT / "assets/third-party/patreon" / name for name in ("patreon-symbol.png", "README.md")})
    for source in sources.values():
        project.local_file(ROOT, str(source.relative_to(ROOT)))
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    (destination / "index.html").write_text(version_resources(page, "index.html", sources))
    supporters = public_links(project.supporter_page())
    (destination / "supporters.html").write_text(version_resources(supporters, "supporters.html", sources))
    preview = public_links(project.supporter_page(preview=True))
    (destination / "supporters-preview.html").write_text(version_resources(preview, "supporters-preview.html", sources))
    (destination / ".nojekyll").write_text("")
    for relative, source in sources.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".html":
            # The UI pages keep their ../assets paths because they live under ui/.
            content = source.read_text().replace('href="../dashboard/index.html"', 'href="../index.html"')
            content = content.replace('href="../docs/', f'href="{REPO_URL}docs/')
            target.write_text(version_resources(content, relative, sources))
        else:
            shutil.copy2(source, target)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(f"Exported public page and design previews to {export(ROOT / '_site')}")
