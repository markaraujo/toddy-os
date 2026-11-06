#!/usr/bin/env python3
"""Refuse ISO tool installation before the live-system prerequisite passes."""
from pathlib import Path
import json
import subprocess

subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
states={r['id']:r['status'] for r in json.loads(Path('/opt/toddy-build/status.json').read_text())['milestones']}
if states['H10']!='completed' or states['H11']!='in_progress':
    raise SystemExit('H11 requires H10 completed and H11 in_progress; sync accepted status first')
result=json.loads(Path('/var/log/toddy/build/h09-bootloader.success.json').read_text())
if result['recipe_exit']!=0 or result['postcheck_exit']!=0:
    raise SystemExit('H11 requires actual native bootloader artifact acceptance')
