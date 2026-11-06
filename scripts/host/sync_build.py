#!/usr/bin/env python3
"""Transfer verified build inputs under the same guest lock as recipe execution."""
import hashlib
import inspect
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import vm

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_source(root, name):
    if Path(name).name != name or name in ('.', '..') or any(ord(c)<32 for c in name):
        raise ValueError('Unsafe source filename')
    path = root/'.local/sources'/name
    if path.is_symlink() or not path.is_file():
        raise ValueError('Source cache entry must be a regular file')
    return path


def metadata_filter(info):
    if '__pycache__' in Path(info.name).parts or info.name.endswith('.pyc'):
        return None
    if not (info.isfile() or info.isdir()):
        raise ValueError('Only regular build metadata files/directories may be transferred')
    info.uid = info.gid = 0
    info.uname = info.gname = 'root'
    return info


def verify_bundle(stage):
    marker = stage/'toddy-input-sync.complete.json'
    if marker.is_symlink() or not marker.is_file():
        raise ValueError('Input transfer has no completion manifest')
    expected = json.loads(marker.read_text())
    actual = {}
    files = []
    for path in stage.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Unexpected input file type')
        if not path.is_file() or path == marker:
            continue
        relative = path.relative_to(stage).as_posix()
        if not relative.startswith(('opt/toddy-build/','mnt/lfs/sources/')):
            raise ValueError('Unexpected input namespace')
        with path.open('rb') as stream:
            actual[relative] = hashlib.file_digest(stream,'sha256').hexdigest()
        files.append(path)
    if expected != {'schema_version':1,'files':actual}:
        raise ValueError('Input transfer incomplete or corrupted')
    return files


def stream_inputs(stream, root, metadata, sources, references):
    files = {}
    def tracked_filter(source_base,archive_base):
        def capture(info):
            info = metadata_filter(info)
            if info is not None and info.isfile():
                source = source_base/Path(info.name).relative_to(archive_base)
                files[info.name] = digest(source)
            return info
        return capture
    with tarfile.open(fileobj=stream, mode='w|') as archive:
        for name in metadata:
            archive_base = 'opt/toddy-build/'+name
            archive.add(root/name, arcname=archive_base,
                        filter=tracked_filter(root/name,archive_base))
        for name in sources:
            path = safe_source(root,name)
            archive_base = 'mnt/lfs/sources/'+name
            archive.add(path, arcname=archive_base, filter=tracked_filter(path,archive_base))
        for kind,path in references:
            archive_base = 'mnt/lfs/sources/evidence/h07-'+kind+'/reference.log'
            archive.add(path, arcname=archive_base, filter=tracked_filter(path,archive_base))
        data = json.dumps({'schema_version':1,'files':files},sort_keys=True).encode()
        marker = tarfile.TarInfo('toddy-input-sync.complete.json')
        marker.size = len(data)
        marker.mode = 0o644
        marker.uname = marker.gname = 'root'
        archive.addfile(marker,io.BytesIO(data))


def main():
    lock = json.loads((ROOT/'config/sources.lock.json').read_text())
    if lock['status'] != 'verified':
        raise SystemExit('Source lock not verified')
    rows = list(lock['packages'])
    metadata = ['scripts/build','LICENSES','config/component-licenses.json',
                'config/books.lock.json','config/sources.lock.json']
    if (ROOT/'config/vim-glvs-inputs.lock.json').exists():
        metadata.append('config/vim-glvs-inputs.lock.json')
    for filename,required in [('security-overlay.lock.json','frozen_for_final_build'),
                              ('supplemental-sources.lock.json','frozen_for_native_build')]:
        path = ROOT/'config'/filename
        if path.exists():
            data = json.loads(path.read_text())
            if data['status'] != required:
                raise SystemExit('Selected source additions are not frozen')
            rows += data['components']
            metadata.append('config/'+filename)
    sources = {}
    for row in rows:
        path = safe_source(ROOT,row['filename'])
        if digest(path) != row['sha256']:
            raise SystemExit('Source mismatch before transfer: '+row['filename'])
        if row['filename'] in sources and sources[row['filename']] != row['sha256']:
            raise SystemExit('Conflicting source pins')
        sources[row['filename']] = row['sha256']
    references = []
    for kind,filename in [('gcc','compiler-test-reference.json'),('bash','bash-test-reference.json')]:
        config_path = ROOT/'config'/filename
        if config_path.exists():
            config = json.loads(config_path.read_text())
            if len(config['sha256']) != 64 or any(c not in '0123456789abcdef' for c in config['sha256']):
                raise SystemExit('Invalid test reference hash')
            path = ROOT/'.local/references'/(kind+'-reference-'+config['sha256']+'.log')
            if not path.is_file() or digest(path) != config['sha256']:
                raise SystemExit('Fetch the pinned '+kind+' reference before syncing')
            metadata.append('config/'+filename)
            references.append((kind,path))
    # Lock the entire receive operation, including the pre-snapshot interval
    # before a runner creates running.json. A failed partial transfer leaves a
    # marker which blocks recipe dispatch until a complete resync succeeds.
    receive = r'''set -euo pipefail
if compgen -G '/var/log/toddy/build/*.running.json' > /dev/null; then
 echo 'Refusing input sync during an unfinished recipe' >&2; exit 1
fi
work=$(mktemp -d /opt/toddy-input-sync.XXXXXX)
trap 'rm -rf -- "$work"' EXIT
tar --no-same-owner --no-overwrite-dir -xf - -C "$work"
# Finish the short local commit if the SSH client disconnects after upload.
trap '' HUP
python3 - "$work" <<'APPLY'
from pathlib import Path
import hashlib,json,os,shutil,sys
__VERIFY_BUNDLE_SOURCE__
stage=Path(sys.argv[1])
files=verify_bundle(stage)
Path('/var/log/toddy/build/input-sync.running').write_text('Verified input commit unfinished; rerun sync before dispatch.\n')
dispatcher='opt/toddy-build/scripts/build/run_step.py'
files.sort(key=lambda p:(str(p.relative_to(stage))!=dispatcher,str(p)))
for source in files:
 relative=source.relative_to(stage)
 text=relative.as_posix()
 if not (text.startswith('opt/toddy-build/') or text.startswith('mnt/lfs/sources/')):
  raise SystemExit('Unexpected input namespace')
 destination=Path('/')/relative
 allowed=Path('/opt/toddy-build') if text.startswith('opt/') else Path('/mnt/lfs/sources')
 if not destination.resolve().is_relative_to(allowed):
  raise SystemExit('Input destination escapes its guarded namespace')
 destination.parent.mkdir(parents=True,exist_ok=True)
 temporary=destination.with_name(destination.name+'.input-sync-part')
 if temporary.exists() or temporary.is_symlink():
  raise SystemExit('Previous partial input exists; inspect before resuming')
 shutil.copy2(source,temporary,follow_symlinks=False)
 os.replace(temporary,destination)
APPLY
rm /var/log/toddy/build/input-sync.running
'''
    receive = receive.replace('__VERIFY_BUNDLE_SOURCE__',inspect.getsource(verify_bundle))
    command = ('source /opt/toddy-build/scripts/build/target.sh; guard_target; '
               'mkdir -p /var/log/toddy/build; '
               'flock -n -E 75 /var/log/toddy/build/build.lock bash --noprofile --norc -c '+shlex.quote(receive))
    process = subprocess.Popen(vm.ssh_args()+[command], stdin=subprocess.PIPE)
    error = None
    try:
        stream_inputs(process.stdin, ROOT, metadata, sources, references)
    except (BrokenPipeError, OSError, ValueError) as exc:
        error = exc
    finally:
        try:
            process.stdin.close()
        except BrokenPipeError:
            pass
    result = process.wait()
    if result == 75:
        raise SystemExit('Refusing full input sync: a recipe owns the guest build lock')
    if error or result:
        raise SystemExit(f'Input transfer incomplete (receiver={result}): {error}; inspect input-sync.running')
    print('Verified build inputs transferred under exclusive lock; source directory mode preserved.')


if __name__ == '__main__':
    main()
