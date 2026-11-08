#!/usr/bin/env python3
"""Ephemeral system credential probe; native disposable target only, never install."""
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zlib


CONSUMER_SOURCE = None
REUSED_NATIVE_PROOF = None


def command(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=90, **kwargs)


def output(args):
    r=command(args);assert r.returncode==0,(args,r.returncode,r.stderr)
    return r.stdout.strip()


def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/'])
    assert re.fullmatch(r'/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/'])=='ext4'
    work=Path('/sources/phase2/work/bubblewrap-1')
    source=Path('/sources/phase2/inputs/bubblewrap-0.11.2')
    binary=work/'compile/bwrap'
    assert hashlib.sha256(binary.read_bytes()).hexdigest()=='f36c7341c009446dc7b79417d6baaa9ec583eccb9690553dd53e4d22ac19869f'
    assert source.stat().st_uid==0 and work.stat().st_uid==101
    before={}
    for p in (work/'compile').rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4)==b'\x7fELF':
                    f.seek(0);before[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
    assert before and not list((work/'stage').iterdir())
    env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp',
         'BWRAP':str(binary),'G_TEST_SRCDIR':str(source),
         'G_TEST_BUILDDIR':str(work/'compile'),'BWRAP_MUST_WORK':'1'}
    def no_new_privileges():
        assert os.geteuid()==101 and os.getegid()==101
        assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
        status=Path('/proc/self/status').read_text()
        assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status
    runs=[]
    # Private /var/tmp belongs to the disposable runtime root, never a host path.
    assert isinstance(CONSUMER_SOURCE,str) and CONSUMER_SOURCE
    tests=[('namespace-consumer',['python3','-B','-c',CONSUMER_SOURCE,str(binary)])]
    names=['test-run.sh','test-specifying-pidns.sh','test-specifying-userns.sh']
    if REUSED_NATIVE_PROOF is not None:
        assert REUSED_NATIVE_PROOF['kernel']==os.uname().release and REUSED_NATIVE_PROOF['binary_sha256']==hashlib.sha256(binary.read_bytes()).hexdigest()
        assert {r['name'] for r in REUSED_NATIVE_PROOF['runs']}=={'test-specifying-pidns.sh','test-specifying-userns.sh'}
        assert all(r['exit']==0 for r in REUSED_NATIVE_PROOF['runs'])
        names=['test-run.sh']
    with tempfile.TemporaryDirectory(prefix='toddy-bwrap-runtime-') as temporary:
        os.chown(temporary,101,101)
        fixture=Path(temporary)/'fixture'
        fixture.mkdir()
        shutil.copytree(source/'tests',fixture/'tests')
        helper=fixture/'tests/libtest.sh';original=helper.read_bytes()
        assert Path('/lib64').is_dir() and not Path('/usr/lib64').exists()
        old=b'--symlink usr/lib64 /lib64';assert original.count(old)==1
        helper.write_bytes(original.replace(old,b'--ro-bind /lib64 /lib64'))
        patch={'file':'tests/libtest.sh','before_sha256':hashlib.sha256(original).hexdigest(),
               'after_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
               'reason':'Private runtime fixture uses actual LFS /lib64 directory; original assertion-bearing driver code unchanged'}
        for name in names:
            assert (fixture/'tests'/name).read_bytes()==(source/'tests'/name).read_bytes()
        env['G_TEST_SRCDIR']=str(fixture)
        tests += [(n,['bash',str(fixture/'tests'/n)]) for n in names]
        if REUSED_NATIVE_PROOF is None:
            tests.append(('optional-python-seccomp',['python3','-B',str(source/'tests/test-seccomp.py')]))
        for name,args in tests:
            r=command(args,env=env,cwd=temporary,user=101,group=101,extra_groups=[],preexec_fn=no_new_privileges)
            # Never retain accidental password-hash lines from a failing security
            # regression; only sanitized data enters the public serial channel.
            def sanitize(text):
                return re.sub(r'(?m)^([^:\n]+):(?:\$[^:\n]+|[!*][^:\n]*):[^\n]*$',r'\1:[REDACTED]',text)
            runs.append({'name':name,'exit':r.returncode,'stdout':sanitize(r.stdout),'stderr':sanitize(r.stderr)})
    for relative,digest in before.items():
        with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    raw=json.dumps({'scope':'Native Toddy kernel bwrap namespace/original affected shell drivers; no graphical/ISO/hardware acceptance',
                    'kernel':os.uname().release,'pid1':'systemd','root_source':device,
                    'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
                    'existing_compiled_elf_files_unchanged':len(before),'runs':runs,'reused_native_proof':REUSED_NATIVE_PROOF,'private_fixture_patch':patch},sort_keys=True).encode()
    compressed=zlib.compress(raw,9);encoded=base64.b64encode(compressed).decode()
    chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    success=all(r['exit']==0 for r in runs)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert success,'Native failures remain failures; preserve original report'


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise
