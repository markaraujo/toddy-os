"""Run five unchanged Polkit drivers with native user/mount namespaces."""
import base64,hashlib,json,os,re,subprocess,zlib
from pathlib import Path

def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/sys/fs/cgroup'])=='cgroup2'
    fixture=Path('/sources/phase2/native-fixtures/polkit-suite-1');accepted=json.loads((fixture/'accepted.json').read_text())
    def verify():
        for name,row in accepted['files'].items():
            p=Path('/')/name
            if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
            else:assert p.is_symlink() and str(p.readlink())==row['symlink']
    verify()
    for original,destination in [(Path('/')/accepted['source'],Path('/src')),(Path('/')/accepted['work'],Path('/build'))]:
        assert not destination.exists();destination.mkdir()
        subprocess.run(['mount','--bind',str(original),str(destination)],check=True)
        subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(destination)],check=True)
    runs=[]
    for row in accepted['tests']:
        env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1',**row['env']}
        assert row['cmd'][0]=='/src/test/wrapper.py'
        def drop_user():
            os.setgroups([]);os.setgid(101);os.setuid(101)
        r=subprocess.run(row['cmd'],env=env,cwd='/tmp',preexec_fn=drop_user,capture_output=True,text=True,timeout=row['timeout']+30)
        combined=r.stdout+'\n'+r.stderr
        runs.append({'name':row['name'],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'skip_diagnostics':[line for line in combined.splitlines() if re.search('skipp',line,re.I)]})
    verify()
    success=len(runs)==5 and all(r['exit']==0 and not r['skip_diagnostics'] for r in runs)
    raw=json.dumps({'scope':'Five original Polkit drivers on native Toddy kernel; backend uses mock private bus, not real authorization/helper/desktop acceptance','kernel':os.uname().release,'pid1':'systemd','fixture_manifest_sha256':digest(fixture/'accepted.json'),'unchanged_fixture_files':len(accepted['files']),'runs':runs},sort_keys=True).encode()
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert success,'Original native failures retained; not qualified'
if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise
