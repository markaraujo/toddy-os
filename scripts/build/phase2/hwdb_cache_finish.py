"""Correct only an accidentally valid negative lookup fixture; keep compiled cache."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import textwrap

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(build):
    assert os.getuid()==101
    w=Path('/build');out=w/'probe-2';out.mkdir();cache=w/'hwdb-root/usr/lib/udev/hwdb.bin';before=sha(cache)
    source=(w/'consumer.c').read_text();assert source.count('acpi:ZZZ_INVALID_TODDY:')==1
    (out/'consumer.c').write_text(source.replace('acpi:ZZZ_INVALID_TODDY:','acpi:__TODDY_INVALID_PNP__:'))
    subprocess.run(['cc','-Wall','-Wextra','-Werror',str(out/'consumer.c'),'-lsystemd','-o',str(out/'consumer')],check=True)
    with (out/'consumer.log').open('xb') as log:r=subprocess.run([str(out/'consumer'),str(cache)],stdout=log,stderr=subprocess.STDOUT)
    (out/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0 and sha(cache)==before
    inputs={p.name:sha(p) for p in Path('/usr/lib/udev/hwdb.d').glob('*.hwdb')}
    tail="    out=w/'stage/usr/lib/udev'"+build.split("    out=w/'stage/usr/lib/udev'",1)[1]
    import shutil
    exec(textwrap.dedent(tail),{'w':w,'cache':cache,'inputs':inputs,'sha':sha,'shutil':shutil,'json':json})
    p=w/'test-results.json';d=json.loads(p.read_text());d['probe_recovery']='ZZZ is a real Boca Research vendor wildcard; use syntactically invalid PNP ID for true negative. Existing native cache bytes unchanged, no generator replay.';p.write_text(json.dumps(d,indent=2)+'\n')
