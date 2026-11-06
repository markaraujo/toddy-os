#!/usr/bin/env python3
"""Refuse H09 target changes before actual H08 acceptance and explicit status."""
from pathlib import Path
import json
import subprocess

subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
status=json.loads(Path('/opt/toddy-build/status.json').read_text())
states={r['id']:r['status'] for r in status['milestones']}
if states['H08']!='completed' or states['H09']!='in_progress':
    raise SystemExit('H09 requires H08 completed and H09 in_progress; sync accepted status first')
result=json.loads(Path('/var/log/toddy/build/h08-base-config.success.json').read_text())
if result['recipe_exit']!=0 or result['postcheck_exit']!=0:
    raise SystemExit('H09 requires actual H08 native configuration acceptance')
