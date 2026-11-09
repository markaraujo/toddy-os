"""Native-kernel Glycin tests in a disposable target; no package installation."""
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
import time
import zlib

CONSUMER_SOURCE = None
MIME_COMPAT_SOURCE = None
REUSED_NATIVE_PROOF = None


def output(args):
    return subprocess.check_output(args,text=True,timeout=15).strip()


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/'])=='ext4'
    fixture=Path('/sources/phase2/native-fixtures/glycin-1')
    assert fixture.stat().st_uid==0 and not fixture.is_symlink()
    tests=json.loads((fixture/'test-prepare-results.json').read_text())
    assert tests['test_compile_exit']==0 and not tests['package_promotable']
    for row in tests['executables']:assert digest(fixture/'executables'/row['name'])==row['sha256']
    before={str(p.relative_to(fixture)):digest(p) for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()}
    assert isinstance(CONSUMER_SOURCE,str) and CONSUMER_SOURCE
    runs=[];config_compat=[]
    assert isinstance(MIME_COMPAT_SOURCE,str) and MIME_COMPAT_SOURCE
    compat={};exec(compile(MIME_COMPAT_SOURCE,'glycin-mime-compat','exec'),compat)
    if REUSED_NATIVE_PROOF is not None:
        assert REUSED_NATIVE_PROOF['kernel']==os.uname().release
        assert REUSED_NATIVE_PROOF['test_artifacts']==tests['executables']
        assert all(r['exit']==0 for r in REUSED_NATIVE_PROOF['runs'])
    def no_new_privileges():
        assert os.geteuid()==101 and os.getegid()==101
        assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
        s=Path('/proc/self/status').read_text()
        assert 'NoNewPrivs:\t1' in s and 'CapEff:\t0000000000000000' in s
    with tempfile.TemporaryDirectory(prefix='toddy-glycin-native-') as tmp:
        tmp=Path(tmp);os.chown(tmp,101,101)
        # Private writable data/config/outputs in this disposable runtime root.
        stage=tmp/'stage';shutil.copytree(fixture/'stage',stage,symlinks=True)
        config=stage/'usr/share/glycin-loaders/2+/conf.d/glycin-image-rs.conf'
        original=config.read_bytes();updated=compat['add_dds_canonical_alias'](original)
        config.write_bytes(updated)
        config_compat.append({'path':'usr/share/glycin-loaders/2+/conf.d/glycin-image-rs.conf',
                              'before_sha256':hashlib.sha256(original).hexdigest(),
                              'after_sha256':hashlib.sha256(updated).hexdigest(),
                              'change':'Add canonical image/vnd.ms-dds alias with exact same existing DDS loader; every other configuration entry unchanged'})
        for config in (stage/'usr/share/glycin-loaders/2+/conf.d').glob('*.conf'):
            env=dict(os.environ,DESTDIR=str(stage),CONFIG_FILE='/usr/share/glycin-loaders/2+/conf.d/'+config.name)
            helper=Path('/sources/phase2/inputs/glycin-2.1.5/project/build-aux/setup-integration-test.py')
            r=subprocess.run(['python3','-B',str(helper)],env=env,capture_output=True,text=True,timeout=15)
            runs.append({'name':'setup-integration-test-'+config.stem,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
            assert r.returncode==0
        cwd=tmp/'tests';cwd.mkdir();os.chown(cwd,101,101)
        (cwd/'test-images').symlink_to(fixture/'tests/test-images',target_is_directory=True)
        (cwd/'failures').mkdir();os.chown(cwd/'failures',101,101)
        native_tmp=Path('/build/compile/cargo-target/tests/tmp')
        assert not Path('/build').exists(),'Disposable native test-only path must be absent'
        native_tmp.mkdir(parents=True);os.chown(native_tmp,101,101)
        env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(tmp),'XDG_CACHE_HOME':str(tmp/'cache'),
             'GLYCIN_DATA_DIR':str(stage/'usr/share'),'GI_TYPELIB_PATH':str(stage/'usr/lib/girepository-1.0'),
             'LD_LIBRARY_PATH':str(stage/'usr/lib'),'RUST_LOG':'warn','PYTHONDONTWRITEBYTECODE':'1'}
        commands=[] if REUSED_NATIVE_PROOF is not None else [('native-GI-bwrap-images',['python3','-B','-c',CONSUMER_SOURCE])]
        for row in tests['executables']:
            if REUSED_NATIVE_PROOF is not None and row['name']!='tests':continue
            args=[str(fixture/'executables'/row['name']),'--test-threads=1','--nocapture']
            if REUSED_NATIVE_PROOF is not None:args+=['--exact','color']
            if row['name']=='encoding':args+=['--skip','write_avif']
            commands.append((row['name'],args))
        deadline=time.monotonic()+420
        for index,(name,args) in enumerate(commands):
            try:
                r=subprocess.run(args,env=env,cwd=cwd,user=101,group=101,extra_groups=[],
                                 preexec_fn=no_new_privileges,capture_output=True,text=True,
                                 timeout=max(1,min(150,deadline-time.monotonic())))
                row={'name':name,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
            except subprocess.TimeoutExpired as error:
                def text(x):return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
                row={'name':name,'exit':None,'timeout_seconds':150,'stdout':text(error.stdout),'stderr':text(error.stderr)}
            runs.append(row)
            print('TODDY_GLYCIN_PROGRESS',name,row['exit'],flush=True)
            if row['exit'] is None:
                runs.extend({'name':n,'exit':None,'not_run':'Previous selected test timed out'}
                            for n,_ in commands[index+1:])
                break
    assert all(digest(fixture/p)==sha for p,sha in before.items())
    raw=json.dumps({'scope':'Native kernel Glycin selected original image/edit/encode tests and forced-bwrap GI consumer; no GNOME or hardware acceptance',
                    'kernel':os.uname().release,'pid1':'systemd','runs':runs,'test_artifacts':tests['executables'],
                    'fixture_files_unchanged':len(before),'unsupported_extensions':tests['unsupported_extensions'],
                    'runtime_exclusions':tests['runtime_exclusions'],'config_compatibility':config_compat,
                    'reused_native_proof':REUSED_NATIVE_PROOF},sort_keys=True).encode()
    assert len(raw)<=4*1024**2
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    success=all(r['exit']==0 for r in runs)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,
          'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert success,'Actual native failures remain failures'


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise
