#!/usr/bin/env python3
"""Permit source-built media dependencies where H10 first needs test media.

This gate does not authorize H11 release assembly or accept either milestone.
"""
import json
from pathlib import Path
import subprocess

subprocess.run(['bash', '-c',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
states = {row['id']: row['status'] for row in
          json.loads(Path('/opt/toddy-build/status.json').read_text())['milestones']}
eligible = (states['H10'] == 'in_progress' or
            (states['H10'] == 'completed' and states['H11'] == 'in_progress'))
if states['H09'] != 'completed' or not eligible:
    raise SystemExit('Media tools require accepted H09 and active H10 or H11')
for step in ('kernel', 'bootloader'):
    record = json.loads((Path('/var/log/toddy/build') /
                         ('h09-' + step + '.success.json')).read_text())
    if record['recipe_exit'] != 0 or record['postcheck_exit'] != 0:
        raise SystemExit('Media tools require actual native ' + step + ' acceptance')
