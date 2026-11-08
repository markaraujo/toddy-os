"""Retire two archive-identical expanded source caches after native acceptance."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    ledger=Path('/var/log/toddy/phase2/native-vendor-source-custody.json')
    assert not ledger.exists(),'Inspect completed/partial retirement and real paths; never replay'
    target=Path('/mnt/lfs');rows=json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components']
    choices=[('cargo-c','cargo-c-tool-0.10.24','cargo-c-vendor'),('librsvg','librsvg-2.62.3','librsvg-vendor')]
    report={'scope':'Expanded authenticated public vendor inputs only; complete source archives, locks/receipts, native packages/compiled tests/logs retained',
            'state':'verifying','sources':[]}
    def save():
        part=ledger.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(report,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(ledger)
    save()
    for package,input_name,source_name in choices:
        success=json.loads(Path('/var/log/toddy/build','b02-'+package+'-install.success.json').read_text())
        assert success['recipe_exit']==success['postcheck_exit']==0
        records=list(Path('/var/log/toddy/packages').glob(package+'_*.json'));assert len(records)==1
        native=json.loads(records[0].read_text());assert native['installed']
        assert sha(Path('/var/cache/toddy/packages')/(records[0].stem+'.deb'))==native['archive_sha256']
        row=next(r for r in rows if r['name']==source_name)
        archive=target/'sources'/row['filename'];assert sha(archive)==row['sha256']
        path=target/'sources/phase2/inputs'/input_name/'vendor'
        assert path.is_dir() and not path.is_symlink() and path.resolve()==path
        assert (path.parent/'toddy-prepared.json').is_file()
        expected={}
        with tarfile.open(archive) as source:
            for m in source:
                parts=Path(m.name).parts;assert parts and parts[0]=='vendor' and '..' not in parts and not Path(m.name).is_absolute()
                if m.isdir():continue
                assert m.isfile(),'Unexpected linked/special vendor artifact'
                relative=str(Path(*parts[1:]));assert relative not in expected
                with source.extractfile(m) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                expected[relative]={'sha256':digest,'bytes':m.size}
        actual={}
        for p in path.rglob('*'):
            assert not p.is_symlink()
            if p.is_file():actual[str(p.relative_to(path))]={'sha256':sha(p),'bytes':p.stat().st_size}
            else:assert p.is_dir()
        assert actual==expected,'Changed/extra/missing public inputs; preserve and diagnose'
        report['sources'].append({'package':package,'path':str(path),'archive':str(archive),
            'archive_sha256':row['sha256'],'native_archive_sha256':native['archive_sha256'],
            'payload_entries':len(actual),'payload_bytes':sum(r['bytes'] for r in actual.values()),
            'manifest_sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'directory_inode':path.stat().st_ino,'state':'verified'})
        save()
    report['state']='verified';fs=os.statvfs(target);report['free_bytes_before']=fs.f_bavail*fs.f_frsize;save()
    for row in report['sources']:
        path=Path(row['path']);assert not path.is_symlink() and path.resolve()==path and path.stat().st_ino==row['directory_inode']
        assert sha(Path(row['archive']))==row['archive_sha256']
        row['state']='retiring';save();shutil.rmtree(path);assert not path.exists()
        row['state']='retired';save()
        (path.parent/'toddy-vendor-retired.json').write_text(json.dumps(row,indent=2)+'\n')
    fs=os.statvfs(target);report['free_bytes_after']=fs.f_bavail*fs.f_frsize
    report['reclaimed_bytes']=report['free_bytes_after']-report['free_bytes_before'];report['state']='complete'
    report['recovery']='Do not rerun retirement/acquisition/build. If a changed Rust slice needs this input, restore only the frozen vendor archive into a new temporary directory, verify full file manifests, apply authenticated public readability, then atomically restore the absent vendor path. Keep the retirement/restore receipts.'
    save();print(json.dumps(report))


if __name__=='__main__':main()
