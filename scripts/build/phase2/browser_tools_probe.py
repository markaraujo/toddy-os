"""Actual unprivileged WASM toolchain and read-only profile qualification."""
from pathlib import Path
import errno
import hashlib
import json
import os
import socket
import subprocess

assert os.getuid()==101 and os.getgid()==101
status=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
assert int(status['CapEff'],16)==int(status['CapPrm'],16)==0
assert status['NoNewPrivs'].strip()=='1'
result=Path('/build/browser-tools-probe.json')
assert not result.exists(),'Never replay qualified compiler probes'
denied=[]
for path in ['/src/.toddy-denied','/usr/.toddy-denied','/etc/.toddy-denied',
             '/tools/wasi-sdk/.toddy-denied','/tools/nasm/.toddy-denied']:
    try:Path(path).write_text('forbidden')
    except OSError as e:
        assert e.errno in (errno.EROFS,errno.EACCES), (path,e)
        denied.append({'path':path,'errno':e.errno})
    else:raise AssertionError('Out-of-scope write succeeded')
for path in ['/tools/wasi-sdk/bin/clang','/tools/nasm/usr/bin/nasm']:
    try:fd=os.open(path,os.O_WRONLY)
    except OSError as e:
        assert e.errno in (errno.EROFS,errno.EACCES), (path,e)
        denied.append({'path':path,'errno':e.errno})
    else:os.close(fd);raise AssertionError('Compiler tool mutation possible')
assert not any(Path(p).exists() for p in ['/root','/mnt/lfs','/sources','/run/dbus'])
with socket.socket() as s:
    try:s.connect(('1.1.1.1',443))
    except OSError as e:network_errno=e.errno
    else:raise AssertionError('Unexpected external route')
compiler='/tools/wasi-sdk/bin/clang';cxx='/tools/wasi-sdk/bin/clang++'
version=subprocess.check_output([compiler,'--version'],text=True)
assert int(version.split('clang version ')[1].split('.')[0])>=19
targets=subprocess.check_output([compiler,'--print-targets'],text=True)
assert 'wasm32' in targets
nasm=subprocess.check_output(['/tools/nasm/usr/bin/nasm','-v'],text=True)
assert 'NASM version 3.02' in nasm
Path('/build/wasi-c.c').write_text('#include <string.h>\nint main(void){return strlen("toddy")==5?0:1;}\n')
Path('/build/wasi-cxx.cc').write_text('#include <cstring>\n#include <string>\nint main(){std::string s="toddy";return s.size()==std::strlen("toddy")?0:1;}\n')
artifacts={}
for language,cc,source in [('c',compiler,'wasi-c.c'),('cxx',cxx,'wasi-cxx.cc')]:
    output=Path('/build/wasi-'+language+'.wasm')
    command=[cc,'--target=wasm32-wasi','--sysroot=/tools/wasi-sdk/share/wasi-sysroot','-O1','/build/'+source,'-o',str(output)]
    completed=subprocess.run(command,capture_output=True,text=True,timeout=60)
    assert completed.returncode==0,(command,completed.stderr)
    data=output.read_bytes();assert data[:8]==b'\0asm\x01\0\0\0' and len(data)>8
    artifacts[language]={'command':command,'exit':completed.returncode,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'wasm_v1_magic':True}
result.write_text(json.dumps({'state':'qualified','uid':os.getuid(),'gid':os.getgid(),
    'caps_effective_permitted':0,'no_new_privileges':True,'denied_writes':denied,
    'external_network_errno':network_errno,'credential_system_paths_absent':True,
    'sdk_clang_version':version,'nasm_version':nasm,'actual_wasm_compile_link':artifacts,
    'scope':'Private build-tool compile/link and isolation qualification, not browser/runtime/hardware acceptance'},indent=2)+'\n')
print(result.read_text())
