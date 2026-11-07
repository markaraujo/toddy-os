#!/usr/bin/env python3
"""Read-only native foundation inventory and unchanged runner scan measurement."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BUILD = Path('/opt/toddy-build/scripts/build')
TARGET = Path('/mnt/lfs')


def output(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def main():
    subprocess.run(['bash', '-c', 'source "$1"; guard_target', 'guard',
                    str(BUILD / 'target.sh')], check=True)
    with Path('/var/log/toddy/build/build.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(Path('/var/log/toddy/build').glob('*.running.json')):
            raise SystemExit('Unreconciled running recipe: inventory cannot nominate it')
        sys.path.insert(0, str(BUILD))
        from run_step import snapshot
        started = time.monotonic()
        files = snapshot()
        elapsed = time.monotonic() - started
        native = ['/usr/sbin/chroot', str(TARGET), '/usr/bin/env', '-i',
                  'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C']
        packages = output(*native, 'dpkg-query', '-W', '-f=${Package}\t${Version}\n')
        audit = output(*native, 'dpkg', '--audit')
        if audit:
            raise SystemExit('Native package audit is not empty')
        check = output(*native, 'apt-get', 'check')
        data = {
            'scope': 'B01-A clone inventory, not desktop/agent/installer acceptance',
            'target_guard': 'passed', 'exclusive_lock': 'available; held during inventory',
            'virtualization': output('systemd-detect-virt'),
            'cpu_count': os.cpu_count(),
            'cpu_model': next(line.split(':', 1)[1].strip() for line in
                              Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),
            'memory': {line.split(':')[0]: line.split(':')[1].strip() for line in
                       Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:'))},
            'target_free_bytes': os.statvfs(TARGET).f_bavail * os.statvfs(TARGET).f_frsize,
            'packages': dict(line.split('\t', 1) for line in packages.splitlines()),
            'dpkg_audit': audit, 'apt_get_check': {'exit': 0, 'output': check},
            'runner_snapshot': {'seconds': round(elapsed, 3), 'entries': len(files),
                'regular_files': sum('sha256' in item for item in files.values()),
                'regular_bytes': sum((TARGET / name.lstrip('/')).lstat().st_size for name, item in files.items() if 'sha256' in item),
                'manifest_sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()},
            'physical_hardware': 'pending',
        }
        print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
