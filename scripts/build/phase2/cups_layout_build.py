"""Fresh affected-input CUPS build with checked paths and deterministic reserves."""
from pathlib import Path
import json
import os
import signal
import subprocess
import time


def main(recipe):
    assert os.getuid() == os.getgid() == 101
    work = Path('/build')
    assert not (work / 'tree').exists() and not (work / 'resource-observation.json').exists()
    assert './configure --prefix=/ ' in recipe and '--prefix=/usr ' not in recipe
    layout_check = """python3 - <<'PYLAYOUT'
from pathlib import Path
import json
text=Path('/build/tree/Makedefs').read_text()
values={line.split('=',1)[0].strip():line.split('=',1)[1].strip() for line in text.splitlines() if '=' in line and not line.startswith('#')}
expected={'prefix':'/','exec_prefix':'/usr','sysconfdir':'/etc','localstatedir':'/var','SERVERROOT':'$(BUILDROOT)/etc/cups','REQUESTS':'$(BUILDROOT)/var/spool/cups','STATEDIR':'$(BUILDROOT)/run/cups'}
assert all(values.get(key)==value for key,value in expected.items()),{key:values.get(key) for key in expected}
Path('/build/layout-configured.json').write_text(json.dumps(expected,indent=2)+'\\n')
PYLAYOUT
"""
    marker = 'make -j4 > /build/original-build.log 2>&1'
    assert recipe.count(marker) == 1
    recipe = recipe.replace(marker, layout_check + marker)
    stage_marker = '# Preserve compiled lp/lpadmin policy'
    assert recipe.count(stage_marker) == 1
    stage_guard = """python3 - <<'PYSPACE'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2+17*1024**2+8*1024**2,'Preserve reserve plus measured stage allocation and metadata margin'
PYSPACE
"""
    recipe = recipe.replace(stage_marker, stage_guard + stage_marker)
    child = subprocess.Popen(['bash', '-euo', 'pipefail', '-c', recipe], start_new_session=True)
    minimum = None
    interrupted = False
    while True:
        state = os.statvfs(work)
        available = state.f_bavail * state.f_frsize
        minimum = available if minimum is None else min(minimum, available)
        result = child.poll()
        if result is not None:
            break
        if available < 512 * 1024**2 + 4 * 1024**2:
            interrupted = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            result = child.returncode
            break
        time.sleep(0.1)
    observation = {'minimum_polled_free_bytes': minimum, 'resource_interrupted': interrupted,
                   'recipe_exit': result, 'reserve_bytes': 512 * 1024**2,
                   'interrupt_margin_bytes': 4 * 1024**2, 'poll_interval_seconds': 0.1}
    (work / 'resource-observation.json').write_text(json.dumps(observation, indent=2) + '\n')
    assert not interrupted and result == 0, observation
    assert (work / 'stage/etc/cups/cupsd.conf').is_file()
    assert (work / 'stage/var/spool/cups').is_dir()
    assert not (work / 'stage/usr/etc').exists() and not (work / 'stage/usr/var').exists()
    print(json.dumps({'corrected_layout': True, 'observation': observation}))
