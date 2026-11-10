"""Read-only source aliases on the existing, qualified Doxygen scratch volume."""
from pathlib import Path
import errno,hashlib,json,os,subprocess,tarfile
from prepare_editorconfig_shared_scratch import manifest as cache_manifest

UUID='ae4347fb-31fd-4193-a333-0a549e144231'
VERSIONS={'cups':('2.4.19','cups-2.4.19'),
          'mitkrb':('1.22.2','krb5-1.22.2'),
          'libqmi':('1.38.0','libqmi-1.38.0'),
          'modemmanager':('1.24.2','ModemManager-1.24.2'),
          'gnome-control-center':('50.4','gnome-control-center-50.4')}

def layout(base,name,version,source_name):
    assert name in VERSIONS and VERSIONS[name]==(version,source_name),'Only exact frozen inputs may use source aliases'
    return base/'toddy-editor-workers'/(name+'-source-1')/source_name,base.parent.parent/'inputs'/source_name

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def fingerprint(base):
    rows=[]
    for p in sorted(base.rglob('*')):
        st=p.lstat()
        value=os.readlink(p) if p.is_symlink() else digest(p) if p.is_file() else None
        rows.append((str(p.relative_to(base)),st.st_mode,st.st_uid,st.st_gid,value))
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()

def save(path,state):
    part=path.with_suffix('.part');assert not part.exists()
    with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(path)

def volume(base):
    assert base.resolve()==base
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(base)],text=True).strip()==UUID
    parent=base/'toddy-editor-workers';assert parent.is_dir() and not parent.is_symlink()
    assert parent.stat().st_uid==0 and parent.stat().st_mode&0o777==0o700

def check_alias(source,target):
    assert target.resolve()==target and source.resolve()==source
    assert source.stat().st_ino==target.stat().st_ino and source.stat().st_dev==target.stat().st_dev
    flags=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(target)],text=True).strip().split(','))
    assert {'ro','nosuid','nodev'}<=flags

def bind(source,target):
    assert source.resolve()==source and target.resolve()==target and not list(target.iterdir())
    assert subprocess.run(['mountpoint','-q',str(target)]).returncode==32
    subprocess.run(['mount','--bind',str(source),str(target)],check=True)
    subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(target)],check=True)
    check_alias(source,target)

def begin(row,source_name):
    assert os.geteuid()==0
    base=Path('/mnt/lfs/sources/phase2/work/doxygen-1');volume(base)
    source,target=layout(base,row['name'],row['version'],source_name)
    receipt=Path('/var/log/toddy/phase2')/(row['name']+'-input-scratch-1.json')
    assert not receipt.exists() and not source.parent.exists() and not target.exists(),'Inspect existing preparation; never replay'
    assert digest(Path('/mnt/lfs/sources')/row['filename'])==row['sha256']
    with tarfile.open(Path('/mnt/lfs/sources')/row['filename']) as archive:
        assert sum(m.size for m in archive if m.isfile())<=64*1024**2
    s=os.statvfs(base);assert s.f_bavail*s.f_frsize>=512*1024**2+64*1024**2
    s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>=16*1024**3+8*1024**2
    before=cache_manifest(base);source.parent.mkdir(mode=0o755)
    state={'state':'source-parent-created','name':row['name'],'version':row['version'],
           'source_name':source_name,'source':str(source),'target':str(target),
           'filesystem_uuid':UUID,'original_cache_manifest':before,
           'archive_filename':row['filename'],'archive_sha256':row['sha256']}
    save(receipt,state)
    return source

def complete(row,source):
    base=Path('/mnt/lfs/sources/phase2/work/doxygen-1');volume(base)
    receipt=Path('/var/log/toddy/phase2')/(row['name']+'-input-scratch-1.json')
    state=json.loads(receipt.read_text());assert state['state']=='source-parent-created' and source==Path(state['source'])
    expected,target=layout(base,row['name'],row['version'],state['source_name']);assert source==expected
    assert json.loads((source/'toddy-prepared.json').read_text())['source_sha256']==row['sha256']
    state.update(state='bind-intended',source_inode=source.stat().st_ino,source_fingerprint=fingerprint(source));save(receipt,state)
    target.mkdir(mode=0o755);bind(source,target)
    try:fd=os.open(target/'.toddy-denied-write',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except OSError as e:assert e.errno==errno.EROFS
    else:os.close(fd);raise AssertionError('Read-only source write unexpectedly succeeded; preserve state')
    assert fingerprint(source)==state['source_fingerprint'] and cache_manifest(base)==state['original_cache_manifest']
    state.update(state='complete',original_cache_unchanged=True,root_write_denied_EROFS=True,
                 recovery='Restore the same source inode/read-only alias after Doxygen, before any compiler; no extraction/preparation replay')
    save(receipt,state)

def restore_inputs(base,log,name):
    selected=[log/(n+'-input-scratch-1.json') for n in VERSIONS if (log/(n+'-input-scratch-1.json')).exists()]
    if not selected:return []
    volume(base);receipt=log/(name+'-source-inputs.json');assert not receipt.exists()
    rows=[]
    for p in selected:
        r=json.loads(p.read_text());assert r['state']=='complete' and r['filesystem_uuid']==UUID
        source,target=layout(base,r['name'],r['version'],r['source_name'])
        assert str(source)==r['source'] and str(target)==r['target'] and source.resolve()==source
        assert r['archive_filename']==('cups-2.4.19-source.tar.gz' if r['name']=='cups' else r['source_name']+('.tar.xz' if r['name']=='gnome-control-center' else '.tar.gz'))
        assert source.stat().st_ino==r['source_inode'] and fingerprint(source)==r['source_fingerprint']
        assert digest(Path('/mnt/lfs/sources')/r['archive_filename'])==r['archive_sha256']
        assert target.resolve()==target and not list(target.iterdir()) and subprocess.run(['mountpoint','-q',str(target)]).returncode==32
        rows.append({'source':str(source),'target':str(target),'source_inode':r['source_inode'],'state':'verified'})
    state={'state':'verified','scope':'Existing exact source aliases only; no extraction or filesystem creation','rows':rows};save(receipt,state)
    for row in rows:
        row['state']='bind-intended';save(receipt,state);bind(Path(row['source']),Path(row['target']));row['state']='restored';save(receipt,state)
    state['state']='complete';save(receipt,state);return rows
