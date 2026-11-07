#!/usr/bin/env python3
"""Read-only dependency fault injection; not guest execution or acceptance."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from project import PHASE2_ORDER, next_eligible

ORDER = PHASE2_ORDER


def walk(stories, blocked):
    complete = {s['id'] for s in stories if s['phase'] != 'agentic' and s['status'] == 'completed'}
    by_id = {s['id']: s for s in stories if s['phase'] == 'agentic'}
    visited = []
    while True:
        ready = [name for name in ORDER if name not in complete and name not in blocked
                 and set(by_id[name]['depends_on']) <= complete]
        if not ready:
            break
        selected = ready[0]
        visited.append(selected)
        complete.add(selected)
    return {'simulated_order': visited,
            'pending': [name for name in ORDER if name not in complete],
            'blocked': sorted(blocked)}


def main():
    data = json.loads((ROOT / 'status.json').read_text())
    stories = data['milestones']
    assert {s['id'] for s in stories if s['phase'] == 'agentic'} == set(ORDER)
    # Exercise the actual selector, not only a second topological implementation.
    import copy
    probe = copy.deepcopy(data)
    rows = {s['id']: s for s in probe['milestones']}
    for name in ORDER:
        rows[name]['status'] = 'not_started'
    rows['B01']['status'] = 'completed'
    rows['B03']['status'] = 'blocked'
    assert next_eligible(probe) == 'B02', 'Blocked engine must not starve eligible desktop'
    nominal = walk(stories, set())
    assert not nominal['pending'], 'Dependency cycle or missing prerequisite'
    results = {'scope': 'structural simulation only; assumes each visited story passes, no duration or runtime proof',
               'status_sha256': hashlib.sha256((ROOT / 'status.json').read_bytes()).hexdigest(),
               'actual_approval': data['owner_review']['phase_2_approved'],
               'nominal': nominal,
               'single_story_faults': {name: walk(stories, {name}) for name in ORDER}}
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
