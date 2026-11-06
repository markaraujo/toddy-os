#!/usr/bin/env python3
"""Refuse H08 target changes until actual H07 acceptance and story tracking."""
import json
from pathlib import Path


def require_gate(project,records):
    status=json.loads((project/'status.json').read_text())
    stories={row['id']:row['status'] for row in status['milestones']}
    if stories.get('H07')!='completed' or stories.get('H08')!='in_progress':
        raise SystemExit('H08 requires completed H07 and in_progress H08; sync reviewed project status first')
    marker=json.loads((records/'h07-native-metadata-closure.success.json').read_text())
    if marker.get('recipe_exit')!=0 or marker.get('postcheck_exit')!=0:
        raise SystemExit('H07 native closure acceptance is invalid')

if __name__=='__main__':
    require_gate(Path(__file__).resolve().parents[3],Path('/var/log/toddy/build'))
