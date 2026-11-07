# Public page redesign and preview verification

Date: 2026-11-07. Publication target: https://markaraujo.github.io/toddy-os/.

## Change

Replaced the plain dashboard with a navy project presentation, unchanged mascot,
selectable desktop/assistant/task/installer design images, humorous installer
stories, computed phase progress and all evidence-bearing milestone details.
The foundation download is explicitly command-line/VM-tested; concepts are not
represented as a working graphical ISO. Source of truth remains status.json.

The site remains buildless GitHub Pages with local assets, no fonts/CDN/telemetry,
account backend or new framework. scripts/project.py renders the tracked HTML
from dashboard/template.html; scripts/export_site.py publishes an explicit list
of assets and UI files, not the checkout, archives, credentials or runtime logs.
Updated the existing export allowlist regression to cover the public preview.

## Basic checks

- make dashboard and make site: passed.
- make check: passed; planning/reference/weight/dependency checks plus 184 existing
  repository unit checks (0.168 seconds in the first complete navy run).
- Playwright exported-page pass, 1440x1000 and 390x844: all images decode, no
  JavaScript page errors, no horizontal overflow.
- Four preview buttons change image/copy/link and selected state correctly.
- Phase filters show 13 foundation and 13 agentic stories, All restores 26.
- Preview pages: all four scenes, light-theme switch, installer next/previous
  and last-slide boundary work; mobile scenes remain within viewport.
- Semantic navy/light text contrast and original identity checks are in
  navy-brand-preview.md. Full accessibility/physical OS qualification is deferred.

Deployment status is recorded after the GitHub Pages run completes. Browser QA
here verifies a static page, not GNOME, inference, hardware or an OS installer.

## Published result

The initial redesigned page commit 196852e482c711910c6385a65cb4e2fe338340ea
passed both Planning consistency and Publish development dashboard. Pages run
[42390489772](https://github.com/markaraujo/toddy-os/actions/runs/42390489772)
completed successfully; deployment 7623671347 reports success on 2026-11-07.

Browser verification on the public URL loaded the new "Your desktop. Your loyal
sidekick." title, switched to the assistant image and followed its concept link
to /ui/preview.html#quick. After page load, the quick scene and pressed state are
correct. The public page and direct concept link are available without local tools.

A follow-up source-formatting commit makes HTML/CSS maintainable without changing
the artwork or product behavior. Regenerated output remains clean; all 184 local
checks pass (0.169 seconds in the final source-formatting run). No new runtime
package dependency was added to the project or public page.
