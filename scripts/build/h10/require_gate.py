#!/usr/bin/env python3
"""Require accepted kernel/boot preparation before live-system execution."""
from pathlib import Path
import json
import subprocess

subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
states={r['id']:r['status'] for r in json.loads(Path('/opt/toddy-build/status.json').read_text())['milestones']}
if states['H09']!='completed' or states['H10']!='in_progress':
    raise SystemExit('H10 requires H09 completed and H10 in_progress; sync accepted status first')
for step in ('kernel','bootloader'):
    result=json.loads((Path('/var/log/toddy/build')/('h09-'+step+'.success.json')).read_text())
    if result['recipe_exit']!=0 or result['postcheck_exit']!=0:
        raise SystemExit('H10 requires actual native '+step+' acceptance')
