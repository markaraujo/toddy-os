#!/usr/bin/env python3
"""Dependency-free planning checks and offline progress rendering."""
import argparse
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = {"not_started", "in_progress", "blocked", "completed"}
PHASE2_ORDER = ("B01", "B03", "B04", "B05", "B02", "B06", "B11", "B12", "B07", "B08", "B09", "B10", "B13")


def next_eligible(data):
    """Prefer an active checkpoint, then the documented risk-first delivery order."""
    by_id = {row["id"]: row for row in data["milestones"]}
    order = tuple(f"H{i:02d}" for i in range(1, 14)) + PHASE2_ORDER
    eligible = [ident for ident in order if by_id[ident]["status"] != "completed"
                and all(by_id[dep]["status"] == "completed" for dep in by_id[ident]["depends_on"])]
    active = [ident for ident in eligible if by_id[ident]["status"] == "in_progress"]
    runnable = [ident for ident in eligible if by_id[ident]["status"] != "blocked"]
    return next(iter(active or runnable or eligible), "B13")


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
        story = local_file(root, row["story"])
        if row["id"].startswith("B"):
            content = story.read_text()
            criteria = re.search(r"## Acceptance criteria\n(.*?)\n## ", content, re.S)
            actual = re.findall(r"^- \[[ x]\] (.*)$", criteria.group(1), re.M) if criteria else []
            if actual != row["acceptance"]:
                raise ValueError(f"Story/status acceptance mismatch: {row['id']}")
            prerequisites = re.search(r"## Prerequisites\n\s*([^\n]+)", content)
            actual_deps = re.findall(r"\b[HB]\d{2}\b", prerequisites.group(1)) if prerequisites else []
            if actual_deps != row["depends_on"]:
                raise ValueError(f"Story/status dependency mismatch: {row['id']}")
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
    review = data.get("owner_review", {})
    if not isinstance(review, dict) or not isinstance(review.get("phase_2_approved", False), bool):
        raise ValueError("Owner review requires a boolean phase_2_approved field")
    approved = review.get("phase_2_approved") is True
    if approved:
        if data["gates"]["G1"] != "passed" or not review.get("approval_evidence"):
            raise ValueError("Phase 2 approval requires G1 and recorded owner approval evidence")
        if review.get("status") != "approved_for_phase_2":
            raise ValueError("Phase 2 approval requires consistent approved_for_phase_2 review status")
        local_file(root, review["approval_evidence"])
    if any(row["phase"] == "agentic" and row["status"] != "not_started" for row in rows) and not approved:
        raise ValueError("Phase 2 requires explicit recorded owner approval before any B story starts")
    work=data.get('active_work')
    if work:
        if work.get('story') not in by_id or by_id[work['story']]['status'] not in {'in_progress','blocked'}:
            raise ValueError('Active work must describe an unfinished active story')
        for field in ('verified','remaining'):
            if not isinstance(work.get(field),list) or not work[field] or not all(isinstance(s,str) and s for s in work[field]):
                raise ValueError('Active work requires factual '+field+' entries')
        if not work.get('running') or not work.get('verified_at'):
            raise ValueError('Active work requires current activity and verification time')
        local_file(root,work['evidence'])
    return by_id


def percentages(data):
    return {phase: sum(r["weight"] for r in data["milestones"]
                       if r["phase"] == phase and r["status"] == "completed")
            for phase in ("foundation", "agentic")}


def supporter_names_html(names):
    """Names stay text; deterministic depth is decorative, never a paid ranking."""
    items = []
    for i, name in enumerate(names):
        style = f'--offset-x:{(i * 17) % 25 - 12}px;--offset-y:{(i * 11) % 21 - 10}px;--depth:{(i * 13) % 25 + 8}px;--tilt:{(i * 7) % 11 - 5}deg;--delay:-{(i * 3) % 19}s'
        items.append(f'<li style="{style}"><button class="supporter-star" type="button" aria-pressed="false"><span class="star-name">{html.escape(name)}</span></button></li>')
    return '<ul class="supporter-list" data-no-translate>' + ''.join(items) + '</ul>'


def community_html():
    """Render only owner-approved public acknowledgments and public support links."""
    community = json.loads((ROOT / "config/community.json").read_text())
    names = community.get("supporters")
    if not isinstance(names, list) or any(not isinstance(name, str) or not name.strip() or len(name) > 80 for name in names):
        raise ValueError("Supporters must be approved public names, each at most 80 characters")
    if len(set(names)) != len(names):
        raise ValueError("Duplicate supporter name")
    result = supporter_names_html(names) if names else '<p class="supporter-empty">Names appear here only with each supporter&#39;s permission.</p>'
    return result


def patreon_html():
    """Render the owner-approved public creator link."""
    community = json.loads((ROOT / "config/community.json").read_text())
    url = community.get("patreon_url")
    if not url:
        return ""
    if url != "https://www.patreon.com/ToddyOS":
        raise ValueError("Use the owner-approved Toddy OS Patreon creator URL")
    return ('<a class="button patreon-button" href="' + url + '" target="_blank" rel="noopener noreferrer">'
            '<img src="../assets/third-party/patreon/patreon-symbol.png" alt="" width="64" height="36" />'
            '<span>Support on Patreon ↗</span></a>')


def supporter_page():
    """Build the public name wall directly from current community data."""
    template = (ROOT / "dashboard/supporters-template.html").read_text()
    names = community_html()
    return template.replace("{{SUPPORTERS}}", names).replace("{{PATREON}}", patreon_html())


def outputs(data):
    pct = percentages(data)
    text = f"# Toddy OS — Current status\n\nUpdated: {data['updated_at']}\n\n"
    text += f"Bootstrap: {data['bootstrap']}\n\n{data['current_scope']}\n\n"
    text += f"Foundation: **{pct['foundation']}%** · Agentic desktop: **{pct['agentic']}%**\n\n"
    text += f"G1: {data['gates']['G1']} · G2: {data['gates']['G2']} · Next: **{data['next_story']}**\n\n"
    text += "No milestone earns credit without completed acceptance evidence.\n\n"
    active_page=''
    work=data.get('active_work')
    if work:
        row=next(r for r in data['milestones'] if r['id']==work['story'])
        current=pct[row['phase']];projected=current+row['weight']
        explanation=(f"The {current}% phase total counts completed stories only. "
                     f"{row['id']} is still {row['status'].replace('_',' ')}; its {row['weight']} points are not yet counted. "
                     f"Passing this story would raise the phase total to {projected}%.")
        text+=f"## Active story: {row['id']} — {row['title']}\n\n{explanation}\n\nLast verified: {work['verified_at']}\n\n"
        text+='Verified:\n\n'+''.join('- '+item+'\n' for item in work['verified'])
        text+='\nRunning: '+work['running']+'\n\nRemaining:\n\n'+''.join('- '+item+'\n' for item in work['remaining'])
        text+=f"\n[Acceptance evidence]({work['evidence']})\n\n"
        active_page=(f'<section class="active-work" aria-labelledby="active-title"><h2 id="active-title">Active story: {html.escape(row["id"])} — {html.escape(row["title"])}</h2>'
                     f'<p>{html.escape(explanation)}</p><p>Last verified: {html.escape(work["verified_at"])}</p><h3>Verified</h3><ul>'
                     +''.join('<li>'+html.escape(item)+'</li>' for item in work['verified'])
                     +f'</ul><h3>Running</h3><p>{html.escape(work["running"])}</p><h3>Remaining</h3><ul>'
                     +''.join('<li>'+html.escape(item)+'</li>' for item in work['remaining'])
                     +f'</ul><a href="../{html.escape(work["evidence"])}">Acceptance evidence</a></section>')
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
                     f'<p class="technical-note">Technical acceptance criteria (English)</p><ul lang="en" data-no-translate>{criteria}</ul><a href="../{esc(row["story"])}">Open story</a></details>')
    metrics = []
    for phase, title in (("foundation", "LFS foundation"), ("agentic", "Toddy desktop & assistant")):
        if phase == "foundation":
            note = "G1 passed · VM-tested" if data["gates"]["G1"] == "passed" else "Foundation work pending"
        elif data["gates"]["G2"] == "passed":
            note = "Experimental owner preview · see evidence"
        elif any(r["phase"] == "agentic" and r["status"] != "not_started" for r in data["milestones"]):
            note = "Small verified deliveries · see milestone state"
        else:
            note = "Planned · development not started"
        metrics.append(f'<article class="metric">{title}<strong>{pct[phase]}%</strong><small>{note}</small><progress aria-label="{title}" value="{pct[phase]}" max="100"></progress></article>')
    metrics.append(f'<article class="metric">Next step<strong>{esc(data["next_story"])}</strong><small>G1 {esc(data["gates"]["G1"])} · G2 {esc(data["gates"]["G2"])}</small></article>')
    page = (ROOT / "dashboard/template.html").read_text()
    replacements = {"METRICS": "".join(metrics), "SCOPE": esc(data["current_scope"]),
                    "UPDATED": esc(data["updated_at"]), "ACTIVE_WORK": active_page,
                    "STORIES": "".join(cards), "SUPPORTERS": community_html(), "PATREON": patreon_html()}
    for key, value in replacements.items():
        page = page.replace("{{" + key + "}}", value)
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    return {"STATUS.md": text, "dashboard/index.html": page}


def check_links(root=ROOT):
    # Include new project docs, but never traverse ignored source/cache trees.
    result = subprocess.run(['git', 'ls-files', '-co', '--exclude-standard', '-z', '--', '*.md'],
                            cwd=root, check=True, capture_output=True)
    for name in sorted(set(result.stdout.decode().split('\0')) - {''}):
        doc = root / name
        if not doc.is_file():
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
        if data.get('active_work',{}).get('story')==args.story and args.status not in {'in_progress','blocked'}:
            data.pop('active_work')
        if args.evidence:
            row["evidence"] = args.evidence
        by_id = {r["id"]: r for r in data["milestones"]}
        for gate, terminal in (("G1", "H13"), ("G2", "B13")):
            data["gates"][gate] = "passed" if by_id[terminal]["status"] == "completed" else "pending"
        data["next_story"] = next_eligible(data)
    validate(data)
    if args.command in ("render", "set"):
        if args.command == "set":
            (ROOT / "status.json").write_text(json.dumps(data, indent=2) + "\n")
        for name, content in outputs(data).items():
            (ROOT / name).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / name).write_text(content)
        (ROOT / "dashboard/supporters.html").write_text(supporter_page())
        print("Rendered STATUS.md and offline dashboard.")
    elif args.command == "check":
        check_links()
        for name, content in outputs(data).items():
            if not (ROOT / name).exists() or (ROOT / name).read_text() != content:
                raise ValueError(f"Stale generated file: {name}; run make dashboard")
        print("Planning checks passed: 26 stories, dependencies, weights, evidence, book lock, links and generated status.")
    else:
        print(json.dumps({"phase_progress": percentages(data), "next_story": data["next_story"], "gates": data["gates"],
                          "phase_2_execution_allowed": data.get("owner_review", {}).get("phase_2_approved") is True}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise SystemExit(f"Project check failed: {exc}") from exc
