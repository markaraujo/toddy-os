"""Run the two unchanged Systemd core drivers on real native cgroup v2."""
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
    fixture=Path('/sources/phase2/native-fixtures/systemd-pam-1');accepted=json.loads((fixture/'accepted.json').read_text())
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    source=Path(accepted['source']);manifest=json.loads((fixture/'source-manifest.json').read_text())
    assert hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()==accepted['source_manifest_sha256']
    def verify_source():
        for name,row in manifest.items():
            p=source/name
            if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
            else:assert p.is_symlink() and str(p.readlink())==row['symlink']
    verify_source()
    for original,destination in [(source,Path('/src')),(fixture,Path('/build'))]:
        assert not destination.exists();destination.mkdir()
        subprocess.run(['mount','--bind',str(original),str(destination)],check=True)
        subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(destination)],check=True)
    runs=[]
    for row in accepted['tests']:
        assert row['name'] in ['test-load-fragment','test-unit-serialize'] and row['cmd']==['/build/compile/'+row['name']]
        env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8',**row['env']}
        r=subprocess.run(row['cmd'],env=env,cwd='/tmp',capture_output=True,text=True,timeout=row['timeout'])
        combined=r.stdout+'\n'+r.stderr
        runs.append({'name':row['name'],'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'observed_test_headers':len(re.findall(r'^/\* .+ \*/$',combined,re.M)),'skip_diagnostics':[line for line in combined.splitlines() if re.search('skipp',line,re.I)]})
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    verify_source()
    success=all(r['exit']==0 for r in runs)
    raw=json.dumps({'scope':'Two original cgroup-dependent Systemd PAM-build core drivers on native Toddy; no updated PID1/PAMName/session/GNOME acceptance','kernel':os.uname().release,'pid1':'systemd','cgroup_filesystem':'cgroup2','fixture_manifest_sha256':digest(fixture/'accepted.json'),'unchanged_fixture_files':len(accepted['artifacts']),'unchanged_source_files':accepted['source_files'],'source_manifest_sha256':accepted['source_manifest_sha256'],'runs':runs},sort_keys=True).encode()
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert success,'Original native failures retained; not qualified'
if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise
