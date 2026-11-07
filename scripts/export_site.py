#!/usr/bin/env python3
"""Export an explicit public page/design allowlist; never publish the checkout."""
import argparse
import json
import shutil
from pathlib import Path

import project

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/markaraujo/toddy-os/blob/main/"
BRAND_FILES = (
    "toddy-os-system-icon.png", "toddy-os-wallpaper-dark.png",
    "toddy-os-wallpaper-light.png", "toddy-os-boot-background.png",
    "toddy-os-desktop-preview.png", "toddy-os-assistant-preview.png",
    "toddy-os-task-preview.png", "toddy-os-installer-preview.png",
)
UI_FILES = ("tokens.css", "preview.css", "preview.html", "installer-slides.html")


def public_links(content):
    """Keep design pages on Pages, and route repository documentation to GitHub."""
    content = content.replace('src="../assets/', 'src="assets/')
    content = content.replace('href="../ui/', 'href="ui/')
    content = content.replace('href="../assets/', 'href="assets/')
    return content.replace('href="../', f'href="{REPO_URL}')


def export(destination):
    destination = destination.resolve()
    if destination != ROOT / "_site":
        raise ValueError("Export destination must be the project's generated _site directory")
    data = json.loads((ROOT / "status.json").read_text())
    project.validate(data)
    page = public_links(project.outputs(data)["dashboard/index.html"])
    # Validate every source before replacing the previous generated export.
    sources = {"site.css": ROOT / "dashboard/site.css"}
    sources.update({f"assets/brand/{name}": ROOT / "assets/brand" / name for name in BRAND_FILES})
    sources.update({f"ui/{name}": ROOT / "ui" / name for name in UI_FILES})
    for source in sources.values():
        project.local_file(ROOT, str(source.relative_to(ROOT)))
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    (destination / "index.html").write_text(page)
    (destination / ".nojekyll").write_text("")
    for relative, source in sources.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".html":
            # The UI pages keep their ../assets paths because they live under ui/.
            content = source.read_text().replace('href="../dashboard/index.html"', 'href="../index.html"')
            content = content.replace('href="../docs/', f'href="{REPO_URL}docs/')
            target.write_text(content)
        else:
            shutil.copy2(source, target)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(f"Exported public page and design previews to {export(ROOT / '_site')}")
