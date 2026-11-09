"""Retire only native extraction duplicates, retaining artifacts and all G1 proofs."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'h10'))
from copy_selected_root import snapshot,tree_names


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=Path('/var/log/toddy/phase2/verified-extraction-copy-custody.json')
    assert not receipt.exists(),'Inspect actual prior custody; never replay'
    base=Path('/mnt/lfs/sources/stage')
    mounts=[Path(s) for s in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
    record={'scope':'Only two redundant extracted validation trees in disposable target; compressed rootfs/ACL sidecars/manifests/logs/assembly sources/ISOs/immutable backings and historical G1 evidence retained',
            'state':'verifying','recipe_sha256':digest(Path(__file__)),
            'before_free_bytes':shutil.disk_usage('/mnt/lfs').free,'copies':[]}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(record,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save()
    for name in ['h10-live-compression','h11-release-compression']:
        work=base/name;tree=work/'extracted';artifact=work/'rootfs.squashfs'
        assert work.resolve()==work and tree.resolve()==tree and tree.is_dir() and not tree.is_symlink()
        assert work.stat().st_uid==0 and work.stat().st_mode&0o022==0 and tree.stat().st_uid==0
        assert not any(p==tree or p.is_relative_to(tree) for p in mounts)
        report=json.loads((work/'compression.json').read_text())
        assert report['complete'] and report['native_extraction_and_acl_restore_verified'] and report['source_unchanged']
        assert Path(report['artifact'])==artifact and artifact.is_file() and not artifact.is_symlink()
        assert artifact.stat().st_size==report['artifact_bytes'] and digest(artifact)==report['artifact_sha256']
        assert digest(work/'restore_live_acls.sh')==report['helper_sha256']
        assert json.loads((work/'restoration-comparison.json').read_text())['matches']
        expected=json.loads((work/'restored-manifest.json').read_text())
        actual=snapshot(tree,tree_names(tree));assert actual==expected,'Extraction copy differs; preserve it'
        row={'tree':str(tree),'state':'verified','inode':tree.stat().st_ino,'entries':len(actual['entries']),
             'hardlink_groups':len(actual['hardlink_groups']),'artifact':str(artifact),'artifact_sha256':report['artifact_sha256'],
             'restored_manifest_sha256':digest(work/'restored-manifest.json'),'helper_sha256':report['helper_sha256']}
        record['copies'].append(row);save()
        print(json.dumps({'phase':'verified-existing-extraction','name':name,'entries':row['entries']}),flush=True)
    for row in record['copies']:
        tree=Path(row['tree']);assert tree.stat().st_ino==row['inode']
        assert digest(Path(row['artifact']))==row['artifact_sha256']
        row['state']='retiring-verified-duplicate';save()
        shutil.rmtree(tree);assert not tree.exists()
        row['state']='retired-compressed-artifact-and-full-metadata-retained';save()
    record.update(state='complete',after_free_bytes=shutil.disk_usage('/mnt/lfs').free)
    record['reclaimed_bytes']=record['after_free_bytes']-record['before_free_bytes']
    record['recovery']='Verify retained rootfs SHA/helper/restored-manifest first. Extract with the accepted native unsquashfs into a NEW absent private stage, apply retained ACL helper/sidecar, and compare full snapshot/hardlink metadata to restored-manifest. Do not rerun custody/compression/old foundation milestones.'
    save();subprocess.run(['sync'],check=True)
    print(json.dumps({k:record[k] for k in ['state','before_free_bytes','after_free_bytes','reclaimed_bytes']}))


if __name__=='__main__':main()
