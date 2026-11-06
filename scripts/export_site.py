#!/usr/bin/env python3
"""Export only approved public dashboard files; never publish the checkout."""
import argparse
import json
import shutil
from pathlib import Path

import project

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/markaraujo/toddy-os/blob/main/"


def export(destination):
    destination = destination.resolve()
    if destination != ROOT / "_site":
        raise ValueError("Export destination must be the project's generated _site directory")
    data = json.loads((ROOT / "status.json").read_text())
    project.validate(data)
    page = project.outputs(data)["dashboard/index.html"]
    page = page.replace('src="../assets/', 'src="assets/')
    page = page.replace('href="../', f'href="{REPO_URL}')
    page = page.replace('<title>', '<link rel="icon" href="assets/brand/toddy-os-system-icon.png"><title>', 1)
    if destination.exists():
        shutil.rmtree(destination)
    (destination / "assets/brand").mkdir(parents=True)
    (destination / "index.html").write_text(page)
    (destination / ".nojekyll").write_text("")
    shutil.copy2(ROOT / "assets/brand/toddy-os-system-icon.png", destination / "assets/brand/toddy-os-system-icon.png")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(f"Exported public dashboard to {export(ROOT / '_site')}")
