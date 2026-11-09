"""Native-kernel headless compositor/GTK/Libadwaita validation, disposable root only."""
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import tempfile
import time
import zlib

ACCEPTED = None
SUITE_SOURCE = None

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def emit(report):
    raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<=4*1024**2
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    ok=bool(report.get('all_selected_exits_zero'))
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':ok,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert ok,'Native failures retained; no graphical qualification from timeout/absence'
def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/'])=='ext4'
    reference=ACCEPTED;assert isinstance(reference,dict)
    component=reference.get('component','libadwaita');assert component in ['libadwaita','gtksourceview']
    syntax_only=reference.get('syntax_only',False);assert not syntax_only or component=='gtksourceview'
    remaining_syntax=reference.get('remaining_syntax',False);assert not remaining_syntax or syntax_only
    fixture_name='gtksourceview-syntax-valid-1' if remaining_syntax else 'gtksourceview-syntax-1' if syntax_only else 'mutter-1' if component=='libadwaita' else 'gtksourceview-1'
    manifest=Path(reference['manifest']);assert str(manifest)=='/sources/phase2/native-fixtures/'+fixture_name+'/accepted.json'
    assert manifest.is_file() and not manifest.is_symlink() and manifest.stat().st_uid==0 and not manifest.stat().st_mode&0o222
    data=manifest.read_bytes();assert len(data)<256*1024 and hashlib.sha256(data).hexdigest()==reference['manifest_sha256']
    accepted=json.loads(data);assert len(accepted['tests'])==(1 if syntax_only else 67 if component=='libadwaita' else 26)
    assert accepted.get('component','libadwaita')==component

    version='1.9.3' if component=='libadwaita' else '5.20.0'
    work=Path('/sources/phase2/work')/(component+'-1');source=Path('/sources/phase2/inputs')/(component+'-'+version)
    asset_dirs=accepted.get('asset_dirs',['tests' if component=='libadwaita' else 'testsuite'])
    assert asset_dirs==(['testsuite','tests','data'] if syntax_only else ['tests' if component=='libadwaita' else 'testsuite'])
    for path,digest in accepted['artifacts'].items():assert sha(Path(path))==digest
    assets={str(p.relative_to(source)):sha(p) for directory in asset_dirs for p in (source/directory).rglob('*') if p.is_file() and not p.is_symlink()}
    assert hashlib.sha256(json.dumps(assets,sort_keys=True).encode()).hexdigest()==accepted['source_test_assets_sha256']
    assert sha(Path('/usr/share/glib-2.0/schemas/gschemas.compiled'))==accepted['schema_cache_sha256']
    for name,version in [('mutter','50.4-1+toddy1'),('gtk','4.22.4-1+toddy4')]:assert output(['dpkg-query','-W','-f=${Version}',name])==version
    assert not Path('/build').exists() and not Path('/src').exists()
    Path('/build').symlink_to(work,target_is_directory=True);Path('/src').symlink_to(source,target_is_directory=True)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    report={'scope':'Native7.1.8 headless Mutter/Wayland original '+component+' tests only; not GDM/KMS/full GNOME/physical acceptance','component':component,'syntax_only':syntax_only,'remaining_syntax':remaining_syntax,'reused_partial_syntax':accepted.get('reused_partial_syntax'),'reused_native_proof':accepted.get('reused_native_proof'),'kernel':os.uname().release,'pid1':'systemd','uid':101,'manifest_sha256':reference['manifest_sha256'],'accepted_input_sha256':hashlib.sha256(json.dumps(accepted,sort_keys=True).encode()).hexdigest(),'runs':[],'all_selected_exits_zero':False}
    def nnp():
        assert os.geteuid()==101 and os.getegid()==101
        assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
        status=Path('/proc/self/status').read_text();assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status
    with tempfile.TemporaryDirectory(prefix='toddy-native-mutter-') as directory:
        root=Path(directory);os.chown(root,101,101);runtime=root/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,101,101)
        config={'root':str(root),'component':component,'syntax_only':syntax_only,'syntax_cases':accepted.get('syntax_cases'),'source':str(source),'fixture':accepted['fixture'],'tests':accepted['tests'],'test_env':accepted['test_env'],'test_binary_prefix':'/build/compile/'+('tests/' if component=='libadwaita' else 'testsuite/'),'test_library_path':'/build/compile/'+('src' if component=='libadwaita' else 'gtksourceview')+':/build/stage/usr/lib'}
        script=root/'suite.py';assert SUITE_SOURCE.count('CONFIG = None')==1;script.write_text(SUITE_SOURCE.replace('CONFIG = None','CONFIG = '+repr(config)));script.chmod(0o644)
        env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(root),'XDG_RUNTIME_DIR':str(runtime),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'GNOME','LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe','GDK_DISABLE':'vulkan','PYTHONDONTWRITEBYTECODE':'1'}
        args=['dbus-run-session','--','mutter','--wayland','--headless','--virtual-monitor=1280x720','--wayland-display=toddy-native-proof','--','python3','-B',str(script)]
        started=time.monotonic()
        try:
            with (root/'session.log').open('wb') as log:r=subprocess.run(args,env=env,cwd=root,user=101,group=101,extra_groups=[],preexec_fn=nnp,stdout=log,stderr=subprocess.STDOUT,timeout=380)
            report['compositor_exit']=r.returncode
        except subprocess.TimeoutExpired:
            report['compositor_exit']=None;report['timeout_seconds']=380
        report['elapsed_seconds']=round(time.monotonic()-started,3)
        report['compositor_log']=(root/'session.log').read_text(errors='replace')
        result=root/'suite-result.json'
        if result.exists():
            suite=json.loads(result.read_text());report['suite']=suite;report['runs']=suite['runs'];report['all_selected_exits_zero']=report['compositor_exit']==0 and suite.get('all_selected_exits_zero') is True
        else:report['runs']=[{'name':'native-compositor-and-suite','exit':report['compositor_exit'],'missing_suite_result':True}]
        images=[]
        for p in sorted(root.glob('gtk-*.png')):
            data=p.read_bytes();assert data.startswith(b'\x89PNG\r\n\x1a\n') and len(data)<2*1024**2
            images.append({'name':p.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'png_base64':base64.b64encode(data).decode()})
        report['native_client_images']=images
        assert all(sha(Path(p))==digest for p,digest in accepted['artifacts'].items()),'Original native test artifacts changed'
        assert assets=={str(p.relative_to(source)):sha(p) for directory in asset_dirs for p in (source/directory).rglob('*') if p.is_file() and not p.is_symlink()}
        report['source_test_files_unchanged']=len(assets)
        report['artifacts_unchanged']=len(accepted['artifacts'])
        emit(report)
if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise
