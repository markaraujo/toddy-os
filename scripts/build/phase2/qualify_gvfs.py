"""Qualify retained Gvfs output without rewriting its original local test failure."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile

SOURCE_SHA='a8d7744615a488a559302fe0cc8f418d5b44aba3c2ba2163e5a9e6f607c1be9a'
EXCLUDED=('usr/libexec/gvfsd-sftp','usr/share/gvfs/mounts/sftp.mount')

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def qualify(root):
    source=Path('/mnt/lfs/sources/phase2/inputs/gvfs-1.60.2')
    work=Path('/mnt/lfs/sources/phase2/work/gvfs-1');log=Path('/var/log/toddy/phase2')
    archive=Path('/mnt/lfs/sources/gvfs-1.60.2.tar.xz')
    assert digest(archive)==SOURCE_SHA
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_sha256']==SOURCE_SHA and not prepared['source_patches']
    assert digest(source/'toddy-build.sh')==prepared['recipe_sha256']==digest(root/'scripts/build/phase2/gvfs-build.sh')
    assert 'ro' in subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(source)],text=True).strip().split(',')
    with tarfile.open(archive) as bundle:
        names=set()
        for member in bundle.getmembers():
            relative=Path(member.name).relative_to('gvfs-1.60.2')
            path=source/relative
            if member.isfile():
                names.add(str(relative));assert digest(path)==hashlib.file_digest(bundle.extractfile(member),'sha256').hexdigest()
            elif member.issym():assert path.is_symlink() and os.readlink(path)==member.linkname
        actual={str(p.relative_to(source)) for p in source.rglob('*') if p.is_file() and not p.is_symlink()}
        assert actual==names|{'toddy-build.sh','toddy-prepared.json'}
    assert (log/'gvfs-1.exit').read_text().strip()=='1'
    assert (log/'gvfs-local-qualify-2.exit').read_text().strip()=='0'
    job=json.loads((log/'gvfs-local-qualify-2.job.json').read_text())
    assert job['command'][-1]==(root/'scripts/build/phase2/gvfs_local_qualify.py').read_text()
    result=json.loads((work/'stage-results.json').read_text())
    assert result['compile_exit']==result['stage_exit']==0
    assert result['original_cases_passed']==17 and result['original_append_tell_failed']
    assert len(result['reused_original_cases'])==11 and len(result['remaining_original_runs'])==6
    assert all(r['exit']==0 for r in result['remaining_original_runs'])
    assert result['baseline_append_consumer']['exit']==0
    assert 'append_preserves_prior_bytes=true' in result['baseline_append_consumer']['stdout']
    assert 'not ok /write/append-tell' in (work/'outputstream.stdout').read_text()
    assert len(result['artifacts'])==189 and len(result['stage_sha256'])==133
    for name,sha in result['artifacts'].items():assert digest(work/'compile'/name)==sha
    actual={str(p.relative_to(work/'stage')):digest(p) for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
    assert actual==result['stage_sha256']
    return result
