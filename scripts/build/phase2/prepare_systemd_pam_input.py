"""Reuse authenticated accepted source read-only, with a separate compiler work."""
import fcntl,hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
SOURCE=Path('/mnt/lfs/sources/systemd-261.2');INPUT=Path('/mnt/lfs/sources/phase2/inputs/systemd-pam-261.2')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert SOURCE.resolve()==SOURCE and SOURCE.is_dir() and SOURCE.stat().st_uid==0
    archive=Path('/mnt/lfs/sources/systemd-261.2.tar.gz');assert digest(archive)=='ed1059ff964f5df35b6056434cc17cc83f86dc913f10489948a0b19b6081c5ec'
    manifest={};patched=[]
    with tarfile.open(archive) as t:
        for m in t:
            rel=Path(m.name).relative_to('systemd-261.2');p=SOURCE/rel
            if m.isfile():
                original=t.extractfile(m).read()
                if str(rel)=='rules.d/50-udev-default.rules.in':
                    expected=original.replace(b'GROUP="render"',b'GROUP="video"').replace(b'GROUP="sgx", ',b'')
                    assert expected!=original and p.read_bytes()==expected
                    patched.append(str(rel))
                else:assert not p.is_symlink() and p.read_bytes()==original,str(rel)
                manifest[str(rel)]={'sha256':digest(p)}
            elif m.issym():assert p.is_symlink() and str(p.readlink())==m.linkname;manifest[str(rel)]={'symlink':m.linkname}
    assert len([r for r in manifest.values() if 'sha256' in r])==7193 and len(patched)==1
    receipt=LOG/'systemd-pam-input-1.json';assert not receipt.exists() and not INPUT.exists(),'Reconcile prior bind/input receipt, never replay'
    assert json.loads((LOG/'systemd-pam-build-volume.json').read_text())['state']=='mounted'
    baseline=SOURCE/'build';config=(baseline/'config.h').read_text();assert '#define HAVE_PAM 0' in config
    state={'state':'validated','source':str(SOURCE),'input':str(INPUT),'source_sha256':digest(archive),'source_manifest_sha256':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),'authenticated_files':7193,'source_changes':patched,'source_inode':SOURCE.stat().st_ino,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid()}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(receipt)
    save();INPUT.mkdir();state['underlying_input_inode']=INPUT.stat().st_ino;save()
    subprocess.run(['mount','--bind',str(SOURCE),str(INPUT)],check=True)
    subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(INPUT)],check=True)
    assert INPUT.stat().st_ino==SOURCE.stat().st_ino
    options=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(INPUT)],text=True).strip().split(',');assert {'ro','nosuid','nodev'}<=set(options)
    assert 'rw' in subprocess.check_output(['findmnt','-n','-o','OPTIONS','--target',str(SOURCE)],text=True).strip().split(',')
    (LOG/'systemd-pam-source-manifest-1.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state.update(state='complete',mount_options=options,recovery='After actual mount inspection restore only this same source inode bind as ro,nosuid,nodev. Never re-extract or edit accepted source; compiler work stays separate.')
    save();print(json.dumps(state))

def restore():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    state=json.loads((LOG/'systemd-pam-input-1.json').read_text());assert state['state']=='complete'
    assert SOURCE.stat().st_ino==state['source_inode'] and SOURCE.resolve()==SOURCE
    manifest=json.loads((LOG/'systemd-pam-source-manifest-1.json').read_text());assert hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()==state['source_manifest_sha256']
    for name,row in manifest.items():
        p=SOURCE/name
        if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
        else:assert p.is_symlink() and str(p.readlink())==row['symlink']
    mounted=subprocess.run(['mountpoint','-q',str(INPUT)]).returncode
    if mounted==32:
        assert INPUT.stat().st_ino==state['underlying_input_inode'] and not list(INPUT.iterdir())
        subprocess.run(['mount','--bind',str(SOURCE),str(INPUT)],check=True)
        subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(INPUT)],check=True)
    else:assert mounted==0
    assert INPUT.stat().st_ino==SOURCE.stat().st_ino
    options=subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(INPUT)],text=True).strip().split(',');assert {'ro','nosuid','nodev'}<=set(options)
    print(json.dumps({'state':'same-authenticated-source-bind-restored','source_inode':SOURCE.stat().st_ino,'source_files':state['authenticated_files']}))

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--restore']:restore()
    else:
        assert len(sys.argv)==1;main()
