#!/bin/bash
# Frozen BLFS13.1 Duktape2.7.0; bytecode APIs deliberately unavailable (ADR0150).
set -euo pipefail
[[ $(id -u) == 101 && -f /src/src/duktape.c ]]
mkdir /build/compile
cp -a --no-preserve=ownership /src/src /build/compile/
cp /src/Makefile.sharedlibrary /src/duktape.pc.in /build/compile/
python3 - <<'PY'
from pathlib import Path
p=Path('/build/compile/Makefile.sharedlibrary');s=p.read_text();assert s.count('-Os')==3;p.write_text(s.replace('-Os','-O2'))
p=Path('/build/compile/src/duk_config.h');s=p.read_text();old='#define DUK_USE_BYTECODE_DUMP_SUPPORT';assert s.count(old)==1;p.write_text(s.replace(old,'#undef DUK_USE_BYTECODE_DUMP_SUPPORT'))
PY
cd /build/compile
make -f Makefile.sharedlibrary -j2 INSTALL_PREFIX=/usr CFLAGS=-std=gnu99 LDFLAGS='-Wl,--no-as-needed -lm -Wl,--as-needed'
make -f Makefile.sharedlibrary INSTALL_PREFIX=/usr DESTDIR=/stage install
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
base=Path('/build');stage=Path('/stage');records=[]
for library in ['duktape','duktaped']:
 for role,source in [('consumer','/src/toddy-probe.c'),('original-hello','/src/examples/hello/hello.c')]:
  binary=base/(role+'-'+library)
  subprocess.run(['cc','-Wall','-Wextra','-Werror','-I/stage/usr/include',source,'-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib','-l'+library,'-o',str(binary)],check=True)
  r=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
  if role=='consumer':assert json.loads(r.stdout)=={'version':20700,'checks':15,'bytecode_load_dump':'unsupported','recovery':True}
  else:assert r.stdout=='Hello world!\n2+3=5\n'
  records.append({'role':role,'library':library,'exit':r.returncode,'stdout':r.stdout.strip(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()})
 path=stage/'usr/lib'/('lib'+library+'.so.207.20700')
 dynamic=subprocess.check_output(['readelf','-d',str(path)],text=True);assert 'libm.so.6' in dynamic and 'libc.so.6' in dynamic and 'RPATH' not in dynamic and 'RUNPATH' not in dynamic
 assert (stage/'usr/include/duk_config.h').read_bytes()==(base/'compile/src/duk_config.h').read_bytes()
proof={'scope':'Two native shared-library variants: original upstream hello and real C policy/JSON/Unicode/GC/refusal/recovery profile; no full ECMAScript conformance suite is supplied in frozen release; no Polkit authorization acceptance','compile_exit':0,'stage_exit':0,'records':records,'bytecode_load_dump':'Disabled through supported DUK_USE_BYTECODE_DUMP_SUPPORT option in both libraries and installed header; APIs fail unsupported, not silently accepted','stage_sha256':{str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}}
(base/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
