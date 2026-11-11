"""Compile only our diagnostic initramfs in the qualified UID101 sandbox."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
assert os.getuid()==101
(token,)=sys.argv[1:];assert len(token)==32 and all(c in '0123456789abcdef' for c in token)
w=Path('/build');base=w/'boot-fuse-probe-1';assert not base.exists();base.mkdir()
compiled=json.loads((w/'kernel-fuse-build-2/compile-result.json').read_text());assert compiled['exit']==0 and compiled['stop_reason'] is None
assert json.loads((w/'kernel-fuse-build-2/source-verified.json').read_text())['private_and_original_source_unchanged']
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
artifacts=json.loads((w/'kernel-fuse-build-2/artifacts.json').read_text())
for name,sha in artifacts.items():assert digest(w/'merged'/name)==sha
runtime=base/'runtime';runtime.mkdir()
for name in ['dev','proc','sys','tmp']:(runtime/name).mkdir()
shutil.copyfile(w/'merged/drivers/net/dummy.ko',runtime/'dummy.ko')
shutil.copyfile(w/'merged/fs/fuse/fuse.ko',runtime/'fuse.ko')
commands=[['gcc','-static','-O2','-Wall','-Wextra','-Werror','-DPROBE_TOKEN="'+token+'"','/src/toddy-fuse-init.c','-o',str(runtime/'init')],['readelf','-l',str(runtime/'init')],['bash','-euc','cd /build/boot-fuse-probe-1/runtime; printf "%s\\0" dev dummy.ko fuse.ko init proc sys tmp | bsdcpio -o --null --format=newc --owner 0:0 --quiet > ../initramfs.cpio'],['bash','-euc','gzip -n -c /build/boot-fuse-probe-1/initramfs.cpio > /build/boot-fuse-probe-1/initramfs.cpio.gz']]
for n,argv in enumerate(commands):
 r=subprocess.run(argv,capture_output=True,timeout=60);(base/(str(n)+'.stdout')).write_bytes(r.stdout);(base/(str(n)+'.stderr')).write_bytes(r.stderr);(base/(str(n)+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0,r.stderr.decode()
 if n==1:assert b'INTERP' not in r.stdout
proof={'scope':'Native static-libc diagnostic initramfs only, not installed OS or Systemd/desktop acceptance','token':token,'kernel_sha256':artifacts['arch/x86/boot/bzImage'],'source_sha256':digest(Path('/src/toddy-fuse-init.c')),'init_sha256':digest(runtime/'init'),'module_sha256':digest(runtime/'dummy.ko'),'fuse_module_sha256':digest(runtime/'fuse.ko'),'initramfs_sha256':digest(base/'initramfs.cpio.gz'),'compile_exit':0,'static_linked':True,'uid':101}
(base/'prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
