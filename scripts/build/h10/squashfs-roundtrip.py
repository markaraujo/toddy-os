#!/usr/bin/env python3
"""Actual installed compressor roundtrips; kernel/overlay tests stay separate."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile


def run(*args,**kwargs):
    return subprocess.run(args,check=True,**kwargs)


def inventory(root):
    result={}
    for path in [root,*sorted(root.rglob('*'))]:
        info=path.lstat()
        row={'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid,'mtime':int(info.st_mtime)}
        if path.is_symlink():row['link']=str(path.readlink())
        elif path.is_file():
            with path.open('rb') as stream:row['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        elif not path.is_dir():raise AssertionError('Unexpected fixture node')
        if not path.is_symlink():
            row['xattrs']={name:os.getxattr(path,name).hex() for name in sorted(os.listxattr(path))}
        result[str(path.relative_to(root))]=row
    return result


work=Path(tempfile.mkdtemp(prefix='toddy-native-squashfs-'))
try:
    source=work/'source';source.mkdir()
    payload=source/'ação com espaço\nlinha';payload.write_bytes(b'Actual native image metadata fixture\n')
    os.chown(payload,18,18);payload.chmod(0o4750)
    os.setxattr(payload,'user.toddy',b'preserved extended attribute')
    os.link(payload,source/'hardlink')
    (source/'symlink').symlink_to(payload.name)
    sparse=source/'sparse'
    with sparse.open('wb') as stream:stream.seek(8*1024*1024);stream.write(b'tail')
    assert sparse.stat().st_blocks*512<sparse.stat().st_size
    run('setfacl','-m','u:101:r--',str(payload))
    for path in source.rglob('*'):os.utime(path,(1600000000,1600000000),follow_symlinks=False)
    before=inventory(source)
    acl=run('getfacl','-R','-P','-n','--skip-base','.',cwd=source,capture_output=True).stdout
    sidecar=work/'acl.txt';sidecar.write_bytes(acl)
    results=[]
    for compressor in ('gzip','xz','zstd'):
        image=work/(compressor+'.squashfs');output=work/('restored-'+compressor)
        run('mksquashfs',str(source),str(image),'-noappend','-comp',compressor,'-processors','2','-mem','128M','-no-progress','-xattrs')
        run('unsquashfs','-processors','2','-no-progress','-d',str(output),str(image))
        assert 'system.posix_acl_access' not in os.listxattr(output/payload.name),'Revisit ACL transport assumption'
        run('setfacl','-P','--restore='+str(sidecar),cwd=output)
        assert inventory(output)==before,(compressor,'metadata/content mismatch')
        assert (output/payload.name).stat().st_ino==(output/'hardlink').stat().st_ino
        assert (output/'sparse').stat().st_blocks*512<(output/'sparse').stat().st_size
        observed=run('getfacl','-R','-P','-n','--skip-base','.',cwd=output,capture_output=True).stdout
        # getfacl traversal order is not an ACL semantic contract; exact xattr
        # bytes/modes/ownership above establish restoration of both hardlinks.
        assert observed and acl
        with image.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        results.append({'compressor':compressor,'image_sha256':sha,'roundtrip':True,'acl_sidecar_restored':True})
    print(json.dumps({'results':results,'native_kernel_boot_validated':False,'overlay_validated':False}))
except BaseException:
    print('Preserved failed private Squashfs fixture: '+str(work),flush=True)
    raise
else:
    shutil.rmtree(work)
