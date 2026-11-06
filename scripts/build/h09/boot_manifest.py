#!/usr/bin/env python3
"""Record/check actual GRUB outputs; never infer boot success from file hashes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys


def snapshot(root):
    files={}
    for base,dirs,names in os.walk(root,followlinks=False):
        for name in dirs+names:
            path=Path(base)/name
            relative=str(path.relative_to(root))
            if path.is_symlink():files[relative]={'link':str(path.readlink())}
            elif path.is_file():
                with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
                files[relative]={'sha256':sha,'size':path.stat().st_size}
            elif not path.is_dir():raise SystemExit('Unexpected boot artifact type: '+relative)
    return files


if __name__=='__main__':
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target; [[ $(findmnt -n -o SOURCE --mountpoint /mnt/lfs/boot/efi) == /dev/vdb2 ]]'],check=True)
    if sys.argv[1:] not in (['write'],['check']):raise SystemExit('Expected write or check')
    with open('/dev/vdb','rb') as stream:mbr=stream.read(512)
    assert mbr[510:]==b'\x55\xaa' and any(mbr[:440]),'Missing BIOS boot sector'
    files=snapshot(Path('/mnt/lfs/boot'))
    for required in ['grub/i386-pc/core.img','grub/i386-pc/normal.mod','grub/x86_64-efi/normal.mod','efi/EFI/BOOT/BOOTX64.EFI']:
        assert files[required]['size']>0,required
    result={'boot_files':files,'mbr_sha256':hashlib.sha256(mbr).hexdigest(),'boot_validated':False,'nvram_modified':False}
    path=Path('/mnt/lfs/sources/evidence/h09-bootloader/artifacts.json')
    if sys.argv[1]=='write':
        with path.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    else:assert json.loads(path.read_text())==result,'Boot artifact changed after installation'
    print('Bootloader artifacts verified; actual BIOS/UEFI boot remains required')
