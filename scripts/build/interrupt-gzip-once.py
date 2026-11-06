#!/usr/bin/env python3
"""H05 controlled failure injection: interrupt only gzip before installation.

Launch once alongside H05. Never run on another target. The script will not
kill a recipe if any gzip target file already exists or its process group
cannot be authenticated against the runner record. Resume is manual after
inspecting the failure manifest; no success is fabricated by this probe.
"""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

if socket.gethostname() != 'toddy-builder':
    raise SystemExit('Wrong guest')
subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
state = Path('/var/log/toddy/build')
trigger = state / 'h05-gzip-interruption-injected.json'
if trigger.exists():
    raise SystemExit('Controlled interruption already recorded; never repeat unchanged')
deadline = time.monotonic() + 1800
while time.monotonic() < deadline:
    marker = state / 'h05-gzip.running.json'
    if not marker.exists():
        time.sleep(2)
        continue
    data = json.loads(marker.read_text())
    pid = data.get('recipe_pid')
    if not pid:
        time.sleep(0.2)
        continue
    time.sleep(1)
    if Path('/mnt/lfs/usr/bin/gzip').exists():
        raise SystemExit('gzip already installed; refusing interruption')
    if os.getpgid(pid) != pid or data['step'] != 'h05-gzip':
        raise SystemExit('Recipe process group mismatch')
    # Prefix executable proves this is the runner's dedicated runuser process.
    command = Path(f'/proc/{pid}/cmdline').read_bytes()
    if not command.startswith(b'/usr/sbin/runuser\0'):
        raise SystemExit('Recipe executable mismatch')
    trigger.write_text(json.dumps({'step': data['step'], 'recipe_pid': pid,
        'reason': 'Controlled interruption before target installation', 'signal': 'SIGTERM'}, indent=2)+'\n')
    os.killpg(pid, signal.SIGTERM)
    print(f'Injected SIGTERM into dedicated gzip recipe group {pid}; inspect failed record before retry.')
    break
else:
    raise SystemExit('gzip did not start before probe deadline')
