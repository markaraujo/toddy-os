"""Archive/restore-verify the obsolete private Firefox object cache before one controlled retirement."""
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot as installed_snapshot
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'h10'))
from copy_selected_root import snapshot,tree_names

SOURCE=Path('/mnt/lfs/sources/phase2/work/firefox-1/build/browser-1/obj')
BASE=SOURCE.parent
RETAINED=BASE/'retained-baseline'
ARTIFACTS={'firefox':'7ade82cb70f1ac513a36e5cfd9b4f6aaa386a0e6bd2808558daf07e10b8ff769','libxul.so':'882296756112c1323ea5d91d6f2f9c21f6b154a6a20456259241a277ccdece20'}
CONTEXT=Path('/var/lib/toddy/phase2-custody/firefox-baseline-objects-1')
RECEIPT=Path('/var/log/toddy/phase2/firefox-baseline-objects-custody-1.json')
TAR_ENV={'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8','HOME':'/root'}


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,data):
    part=path.with_suffix(path.suffix+'.part');assert not part.exists()
    with part.open('x') as f:os.fchmod(f.fileno(),0o600);json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def main():
    assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    assert subprocess.check_output(['findmnt','-n','-o','SOURCE','/'],text=True).strip()=='/dev/vda1'
    assert subprocess.check_output(['lsblk','-dnro','SERIAL','/dev/vda'],text=True).strip()=='TODDY-BUILDER'
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert not RECEIPT.exists() and not CONTEXT.exists(),'Reconcile actual existing archive/extraction/retirement; never replay'
    assert SOURCE.resolve()==SOURCE and SOURCE.is_dir() and not SOURCE.is_symlink() and not (SOURCE/'.toddy-retired.json').exists()
    mounts=[Path(p) for p in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
    assert not any(p==SOURCE or p.is_relative_to(SOURCE) for p in mounts)
    version=subprocess.check_output(['/usr/bin/tar','--version'],env=TAR_ENV,text=True).splitlines()[0];assert version=='tar (GNU tar) 1.35'
    import restore_browser_work as browser
    baseline=json.loads(browser.RECORD.read_text());browser.inspect(baseline)
    compiler=json.loads((BASE/'firefox-compile-result.json').read_text())
    assert compiler['state']=='compiled' and compiler['exit']==0 and compiler['artifacts']==ARTIFACTS
    assert not RETAINED.exists() and not RETAINED.is_symlink()
    for name,expected in ARTIFACTS.items():
        original=SOURCE/'dist/bin'/name
        assert original.resolve().is_relative_to(SOURCE) and sha(original)==expected
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3
    CONTEXT.parent.mkdir(mode=0o700,parents=True,exist_ok=True);assert CONTEXT.parent.resolve()==CONTEXT.parent and CONTEXT.parent.stat().st_uid==0 and not CONTEXT.parent.stat().st_mode&0o022
    CONTEXT.mkdir(mode=0o700)
    state={'scope':'Obsolete uninstalled Firefox153.2 private objects only. Full PAX archive and actual tmpfs restoration compare bytes/metadata/hardlinks before retirement. Exact two ELF artifacts retained separately as non-executable evidence. Source/tools/compiler logs/results and installed system preserved. No browser runtime or whole B02 claim.','state':'snapshotting','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'producer_sha256':sha(Path(__file__)),'source':str(SOURCE),'source_inode':SOURCE.stat().st_ino,'source_uid':SOURCE.stat().st_uid,'source_gid':SOURCE.stat().st_gid,'source_mode':SOURCE.stat().st_mode,'before_target_free':shutil.disk_usage('/mnt/lfs').free,'before_browser_free':shutil.disk_usage(SOURCE).free,'before_builder_free':shutil.disk_usage('/').free,'tar':{'version':version,'sha256':sha(Path('/usr/bin/tar'))}}
    save(RECEIPT,state)
    try:
        before=installed_snapshot();save(CONTEXT/'installed-before.json',before)
        expected=snapshot(SOURCE,tree_names(SOURCE));save(CONTEXT/'source-manifest.json',expected)
        unique={}
        for n,r in expected['entries'].items():
            if 'sha256' in r:
                st=(SOURCE/n).stat();unique[(st.st_dev,st.st_ino)]=st.st_size
        logical=sum(unique.values());assert logical<5*1024**3 and shutil.disk_usage('/').free>=2*1024**3
        archive=CONTEXT/'work.tar.gz';state.update(state='archiving',entries=len(expected['entries']),hardlink_groups=len(expected['hardlink_groups']),unique_regular_bytes=logical,archive=str(archive));save(RECEIPT,state)
        command=['/usr/bin/tar','--create','--file=-','--format=pax','--acls','--xattrs','--xattrs-include=*','--numeric-owner','--sparse','--directory='+str(SOURCE),'.']
        with (CONTEXT/'create.log').open('xb') as errors:
            process=subprocess.Popen(command,env=TAR_ENV,stdout=subprocess.PIPE,stderr=errors)
            try:
                with archive.open('xb') as raw:
                    os.fchmod(raw.fileno(),0o600)
                    class Bounded:
                        def write(self,data):
                            assert raw.tell()+len(data)<=2*1024**3,'Archive budget reached; preserve original and partial artifact'
                            assert shutil.disk_usage('/').free>=1024**3+len(data),'Preserve restoration capacity'
                            return raw.write(data)
                        def flush(self):raw.flush()
                    with gzip.GzipFile(fileobj=Bounded(),mode='wb',filename='',mtime=0,compresslevel=6) as packed:
                        while block:=process.stdout.read(8*1024**2):packed.write(block)
                    raw.flush();os.fsync(raw.fileno())
                code=process.wait();state['archive_create_exit']=code;assert code==0,'Original source/archive changed or tar failed'
            finally:
                process.stdout.close()
                if process.poll() is None:process.terminate();process.wait()
        assert snapshot(SOURCE,tree_names(SOURCE))==expected,'Source cache changed during archive creation'
        state.update(state='extracting',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size);save(RECEIPT,state)
        memory=CONTEXT/'restore-memory';memory.mkdir(mode=0o700)
        available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
        assert available>=logical+4*1024**3,'Preserve guest memory; original source remains'
        state.update(state='mounting-restore-memory',memory=str(memory));save(RECEIPT,state)
        subprocess.run(['mount','-t','tmpfs','-o','size=6G,noswap,nosuid,nodev,noexec,mode=0700','tmpfs',str(memory)],check=True)
        assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(memory)],text=True).strip()=='tmpfs'
        restored=memory/'restored';restored.mkdir(mode=0o700)
        with (CONTEXT/'extract.log').open('xb') as log:
            r=subprocess.run(['/usr/bin/tar','--extract','--gzip','--file='+str(archive),'--directory='+str(restored),'--acls','--xattrs','--xattrs-include=*','--numeric-owner','--same-owner','--same-permissions','--delay-directory-restore'],env=TAR_ENV,stdout=log,stderr=subprocess.STDOUT)
        state['archive_extract_exit']=r.returncode;assert r.returncode==0
        actual=snapshot(restored,tree_names(restored));save(CONTEXT/'restored-manifest.json',actual)
        assert actual==expected,'Actual recovery bytes/metadata/hardlinks differ; preserve original'
        assert snapshot(SOURCE,tree_names(SOURCE))==expected and SOURCE.stat().st_ino==state['source_inode']
        assert sha(archive)==state['archive_sha256']
        state.update(state='restore-verified',source_unchanged=True,restored_exact=True,manifest_sha256=sha(CONTEXT/'source-manifest.json'));save(RECEIPT,state)
        # Preserve private evidence artifacts before retiring the verified cache.
        RETAINED.mkdir(mode=0o700)
        for name,expected_hash in ARTIFACTS.items():
            dst=RETAINED/name
            shutil.copyfile(SOURCE/'dist/bin'/name,dst);dst.chmod(0o444)
            assert sha(dst)==expected_hash
        state.update(retained_artifacts={n:{'path':str(RETAINED/n),'sha256':v} for n,v in ARTIFACTS.items()})
        save(RECEIPT,state)
        # Both copies were fully compared; retire source children while retaining
        # a clear marker at the exact work path. Never touch installed SDK paths.
        state['state']='retiring-obsolete-private-objects';save(RECEIPT,state)
        for p in list(SOURCE.iterdir()):
            if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
            else:p.unlink()
        (SOURCE/'.toddy-retired.json').write_text(json.dumps({'receipt':str(RECEIPT),'archive':str(archive),'archive_sha256':state['archive_sha256'],'source_manifest_sha256':state['manifest_sha256']},indent=2)+'\n')
        assert {p.name for p in SOURCE.iterdir()}=={'.toddy-retired.json'}
        assert installed_snapshot()==before,'Installed root changed; preserve recovery artifact and diagnose'
        state.update(state='retired-verified-objects',installed_root_changed_paths=0,after_target_free=shutil.disk_usage('/mnt/lfs').free);save(RECEIPT,state)
        shutil.rmtree(restored);assert not restored.exists() and sha(archive)==state['archive_sha256']
        subprocess.run(['umount',str(memory)],check=True);memory.rmdir()
        state.update(state='complete',after_builder_free=shutil.disk_usage('/').free);state['reclaimed_browser_bytes']=shutil.disk_usage(SOURCE).free-state['before_browser_free'];state['recovery']='Verify archive/source-manifest SHA. Restore to a NEW private directory using recorded GNU tar PAX ACL/xattr/owner/permission flags; compare full snapshot and hardlink groups with source-manifest. To restore original work, first reconcile sole .toddy-retired marker/receipt, never overwrite an existing/unknown work tree. Keep archive/manifests/logs; original source/tools/logs and separately retained baseline ELF evidence remain available. Retired objects are never a qualified cache for changed Firefox153.7 sources.';save(RECEIPT,state);browser.inspect(baseline);print(json.dumps({k:state[k] for k in ['state','entries','hardlink_groups','archive_bytes','reclaimed_browser_bytes','installed_root_changed_paths']}),flush=True)
    except BaseException as error:
        state.update(state='failed-preserved',error={'type':type(error).__name__,'message':str(error)});save(RECEIPT,state);raise

if __name__=='__main__':main()
