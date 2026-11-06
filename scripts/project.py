#!/usr/bin/env python3
"""Dependency-free planning checks and offline progress rendering."""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = {"not_started", "in_progress", "blocked", "completed"}


def local_file(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or out-of-repository file: {value}")
    return path


def validate(data, root=ROOT):
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported status schema")
    rows = data["milestones"]
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("Duplicate milestone IDs")
    if set(by_id) != {f"{prefix}{i:02d}" for prefix in ("H", "B") for i in range(1, 14)}:
        raise ValueError("Expected H01-H13 and B01-B13")
    for phase in ("foundation", "agentic"):
        if sum(row["weight"] for row in rows if row["phase"] == phase) != 100:
            raise ValueError(f"Weights for {phase} must total 100")
    visited, visiting = set(), set()

    def visit(ident):
        if ident in visiting:
            raise ValueError(f"Dependency cycle at {ident}")
        if ident in visited:
            return
        if ident not in by_id:
            raise ValueError(f"Unknown dependency: {ident}")
        visiting.add(ident)
        for dependency in by_id[ident]["depends_on"]:
            visit(dependency)
        visiting.remove(ident)
        visited.add(ident)

    for row in rows:
        visit(row["id"])
        if row["status"] not in STATES or not isinstance(row["weight"], int) or row["weight"] <= 0:
            raise ValueError(f"Invalid state/weight: {row['id']}")
        expected_phase = "foundation" if row["id"].startswith("H") else "agentic"
        if row["phase"] != expected_phase or not row.get("acceptance"):
            raise ValueError(f"Invalid phase/acceptance: {row['id']}")
        local_file(root, row["story"])
        if row["status"] in {"in_progress", "completed"}:
            if any(by_id[d]["status"] != "completed" for d in row["depends_on"]):
                raise ValueError(f"Unfinished prerequisites: {row['id']}")
        if row["status"] == "completed" and not row["evidence"]:
            raise ValueError(f"Completed milestone has no evidence: {row['id']}")
        for evidence in row["evidence"]:
            local_file(root, evidence)
    books = json.loads((root / "config/books.lock.json").read_text())
    if by_id["H02"]["status"] == "completed":
        if books["status"] != "verified":
            raise ValueError("H02 completion requires a verified book lock")
        for book in ("lfs", "blfs"):
            if not re.fullmatch(r"[a-fA-F0-9]{64}", books[book].get("archive_sha256") or ""):
                raise ValueError(f"Missing actual book SHA-256: {book}")
    if by_id["H02"]["status"] == "completed":
        sources = json.loads((root / "config/sources.lock.json").read_text())
        if sources.get("status") != "verified" or not sources.get("packages"):
            raise ValueError("H02 requires verified source integrity")
        names = set()
        for package in sources["packages"]:
            name = package["filename"]
            if name in names or Path(name).name != name or name in (".", ".."):
                raise ValueError("Invalid or duplicate source filename")
            names.add(name)
            if not re.fullmatch(r"[a-f0-9]{64}", package.get("sha256") or ""):
                raise ValueError(f"Missing frozen SHA-256: {name}")
            if not re.fullmatch(r"[a-f0-9]{32}", package.get("upstream_md5") or ""):
                raise ValueError(f"Missing upstream integrity: {name}")
            if not package["url"].startswith("https://"):
                raise ValueError(f"Insecure source URL: {name}")
    for gate, terminal in (("G1", "H13"), ("G2", "B13")):
        actual = "passed" if by_id[terminal]["status"] == "completed" else "pending"
        if data["gates"][gate] != actual:
            raise ValueError(f"Inconsistent gate {gate}")
    if data["next_story"] not in by_id:
        raise ValueError("Unknown next story")
    return by_id


def percentages(data):
    return {phase: sum(r["weight"] for r in data["milestones"]
                       if r["phase"] == phase and r["status"] == "completed")
            for phase in ("foundation", "agentic")}


def outputs(data):
    pct = percentages(data)
    text = f"# Toddy OS — Current status\n\nUpdated: {data['updated_at']}\n\n"
    text += f"Bootstrap: {data['bootstrap']}\n\n{data['current_scope']}\n\n"
    text += f"Foundation: **{pct['foundation']}%** · Agentic desktop: **{pct['agentic']}%**\n\n"
    text += f"G1: {data['gates']['G1']} · G2: {data['gates']['G2']} · Next: **{data['next_story']}**\n\n"
    text += "No milestone earns credit without completed acceptance evidence.\n\n"
    text += "| Story | Phase | Weight | Status |\n| --- | --- | ---: | --- |\n"
    esc = html.escape
    cards = []
    for row in data["milestones"]:
        text += f"| [{row['id']} — {row['title']}]({row['story']}) | {row['phase']} | {row['weight']} | {row['status']} |\n"
        criteria = "".join(f"<li>{esc(c)}</li>" for c in row["acceptance"])
        cards.append(f'<details data-phase="{esc(row["phase"])}" data-status="{esc(row["status"])}">'
                     f'<summary><span class="id">{esc(row["id"])}</span> {esc(row["title"])} '
                     f'<span class="tag">{esc(row["status"].replace("_", " "))} · {row["weight"]} points</span></summary>'
                     f'<p>Prerequisites: {esc(", ".join(row["depends_on"]) or "None")}</p>'
                     f'<ul>{criteria}</ul><a href="../{esc(row["story"])}">Open story</a></details>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Toddy OS — Development dashboard</title>
<style>
:root{color-scheme:dark;--bg:#171411;--panel:#24201c;--ink:#f6ecdc;--muted:#c1b5a4;--accent:#e6a16c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}
main{max-width:1100px;margin:auto;padding:36px 24px}header{display:flex;gap:24px;align-items:center}
header img{width:90px;height:90px;object-fit:contain}h1{margin:0;font-size:2rem}p{color:var(--muted)}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}.metric{background:var(--panel);padding:22px;border-radius:14px}
.metric strong{display:block;font-size:2rem;color:var(--accent)}progress{width:100%;accent-color:var(--accent)}
nav{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}button{cursor:pointer;background:var(--panel);color:var(--ink);border:1px solid #71604c;border-radius:8px;padding:10px 16px}
button[aria-pressed=true]{background:#704023}button:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
details{background:var(--panel);border:1px solid #44382d;border-radius:10px;margin:10px 0;padding:16px}summary{cursor:pointer}.id{color:var(--accent);font-weight:700}.tag{display:block;color:var(--muted);font-size:.85rem;margin-left:42px}a{color:#ffc28f}footer{margin-top:36px;font-size:.9rem}li{margin:8px 0}
@media(max-width:650px){.metrics{grid-template-columns:1fr}header img{width:65px;height:65px}h1{font-size:1.5rem}}
</style><main><header><img src="../assets/brand/toddy-os-system-icon.png" alt="Toddy OS mascot"><div><h1>Toddy OS</h1><p>Development dashboard · Evidence before progress</p></div></header>
'''
    page += f'<p>{esc(data["current_scope"])}</p><p>Bootstrap: {esc(data["bootstrap"])} · Updated {esc(data["updated_at"])}</p>'
    page += '<section class="metrics" aria-label="Project progress">'
    for phase, title in (("foundation", "LFS foundation"), ("agentic", "Agentic desktop")):
        page += f'<article class="metric">{title}<strong>{pct[phase]}%</strong><progress aria-label="{title}" value="{pct[phase]}" max="100"></progress></article>'
    page += f'<article class="metric">Next milestone<strong>{esc(data["next_story"])}</strong>G1 {esc(data["gates"]["G1"])} · G2 {esc(data["gates"]["G2"])}</article></section>'
    page += '<nav aria-label="Filter milestones"><button data-filter="all" aria-pressed="true">All stories</button><button data-filter="foundation" aria-pressed="false">Phase 1 · Foundation</button><button data-filter="agentic" aria-pressed="false">Phase 2 · Agentic</button></nav>'
    page += '<section aria-label="Milestones">' + "".join(cards) + '</section>'
    page += '<footer><a href="../PRD.md">PRD</a> · <a href="../docs/DEVELOPMENT.md">Development handoff</a><p>Local offline dashboard. No telemetry, API calls or external dependencies. Percentages reflect completed, evidenced weighted milestones.</p></footer></main>'
    page += '''<script>document.querySelectorAll('button[data-filter]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('button[data-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('details[data-phase]').forEach(d=>d.hidden=b.dataset.filter!=='all'&&d.dataset.phase!==b.dataset.filter)}));</script></html>\n'''
    return {"STATUS.md": text, "dashboard/index.html": page}


def check_links(root=ROOT):
    for doc in root.rglob("*.md"):
        if ".git" in doc.parts:
            continue
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            target = target.split("#", 1)[0]
            path = (doc.parent / target).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                raise ValueError(f"Broken local link in {doc.relative_to(root)}: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("check", "render", "progress"):
        sub.add_parser(cmd)
    update = sub.add_parser("set")
    update.add_argument("story")
    update.add_argument("status", choices=sorted(STATES))
    update.add_argument("--evidence", action="append", default=[])
    args = parser.parse_args()
    data = json.loads((ROOT / "status.json").read_text())
    if args.command == "set":
        matches = [r for r in data["milestones"] if r["id"] == args.story]
        if not matches:
            parser.error("Unknown story ID")
        row = matches[0]
        row["status"] = args.status
        if args.evidence:
            row["evidence"] = args.evidence
        by_id = {r["id"]: r for r in data["milestones"]}
        for gate, terminal in (("G1", "H13"), ("G2", "B13")):
            data["gates"][gate] = "passed" if by_id[terminal]["status"] == "completed" else "pending"
        eligible = [r for r in data["milestones"] if r["status"] != "completed" and all(by_id[d]["status"] == "completed" for d in r["depends_on"])]
        data["next_story"] = eligible[0]["id"] if eligible else "B13"
    validate(data)
    if args.command in ("render", "set"):
        if args.command == "set":
            (ROOT / "status.json").write_text(json.dumps(data, indent=2) + "\n")
        for name, content in outputs(data).items():
            (ROOT / name).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / name).write_text(content)
        print("Rendered STATUS.md and offline dashboard.")
    elif args.command == "check":
        check_links()
        for name, content in outputs(data).items():
            if not (ROOT / name).exists() or (ROOT / name).read_text() != content:
                raise ValueError(f"Stale generated file: {name}; run make dashboard")
        print("Planning checks passed: 26 stories, dependencies, weights, evidence, book lock, links and generated status.")
    else:
        print(json.dumps({"phase_progress": percentages(data), "next_story": data["next_story"], "gates": data["gates"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise SystemExit(f"Project check failed: {exc}") from exc
