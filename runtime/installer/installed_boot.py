"""Installed ext4 initramfs using frozen H10 custody/newc validation machinery.

No live overlay init, network, kernel command hook, compiler or host runtime copy.
Actual storage/kernel/BIOS/UEFI qualification is a separate required receipt.
"""
import gzip
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from .disk_plan import InstallError

RELEASE='7.1.8-toddy'
MODULES={'ext4','virtio_pci','virtio_blk','virtio_scsi','sd_mod','nvme','ahci'}
TOOLS=('/usr/sbin/modprobe',)


def machinery():
    try:
        from .h10 import initramfs_runtime,initramfs_archive
    except ImportError:
        from scripts.build.h10 import initramfs_runtime,initramfs_archive
    return initramfs_runtime,initramfs_archive


def init_script(uuid,modules):
    if not isinstance(uuid,str) or not re.fullmatch('[A-Fa-f0-9-]{4,40}',uuid):
        raise InstallError('installer_filesystem_uuid')
    if not isinstance(modules,list) or not modules or len(modules)!=len(set(modules)) or set(modules)-MODULES or 'ext4' not in modules or not set(modules)&(MODULES-{'ext4','virtio_pci'}):
        raise InstallError('installer_boot_storage_profile')
    return ('''#!/bin/bash
# Original Toddy installed ext4 init; no live ISO/overlay or command-line hooks.
export PATH=/usr/bin:/usr/sbin
export LC_ALL=C
rescue() {
    printf '%s\\n' 'Toddy: installed root unavailable; use the retained rescue medium.' > /dev/console
    # A failed PID1 must stay alive. No automatic repair, writes or shell execution.
    while :; do sleep 3600; done
}
mount -t devtmpfs devtmpfs /dev || rescue
mount -t proc proc /proc || rescue
mount -t sysfs sysfs /sys || rescue
mount -t tmpfs -o mode=0755 tmpfs /run || rescue
''' + ''.join('/usr/sbin/modprobe -S '+RELEASE+' '+name+' || rescue\n' for name in modules) + '''ROOT_UUID='''+uuid+'''
root_device=''
# Bounded discovery; a failed wait enters the documented external rescue route.
for ((attempt=0; attempt<60; attempt++)); do
    root_device=$(/usr/sbin/blkid -U "$ROOT_UUID" 2>/dev/null) || root_device=''
    if [[ -b "$root_device" ]] && [[ $(/usr/sbin/blkid -s UUID -o value "$root_device") == "$ROOT_UUID" ]]; then break; fi
    root_device=''
    sleep 1
done
[[ -n "$root_device" ]] || rescue
mount -t ext4 -o ro "$root_device" /newroot || rescue
[[ -x /newroot/usr/lib/systemd/systemd ]] || rescue
mount --move /dev /newroot/dev || rescue
mount --move /proc /newroot/proc || rescue
mount --move /sys /newroot/sys || rescue
mount --move /run /newroot/run || rescue
exec /usr/sbin/switch_root /newroot /usr/lib/systemd/systemd
rescue
''').encode()


def module_namespace(entries):
    prefix='/usr/lib/modules/'+RELEASE
    selected={path:row for path,row in entries.items() if path==prefix or path.startswith(prefix+'/')}
    if not selected or not any(path.endswith('/modules.builtin') for path in selected):
        raise InstallError('installer_boot_module_metadata_missing')
    import json
    return selected,hashlib.sha256((json.dumps(selected,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()


class InstalledBoot:
    def __init__(self,bundle,manifest,profile,system):
        self.bundle=Path(bundle);self.manifest=manifest;self.profile=profile;self.system=system
        if set(profile)!={'kernel_sha256','module_namespace_sha256','modules','epoch'} or type(profile['epoch']) is not int or not 0<=profile['epoch']<=0xffffffff:
            raise InstallError('installer_boot_profile')
        init_script('0000-0000',profile['modules'])
        self.module_entries,namespace=module_namespace(manifest['ownership']['entries'])
        if namespace!=profile['module_namespace_sha256'] or manifest['ownership']['entries'].get('/boot/vmlinuz-'+RELEASE,{}).get('sha256')!=profile['kernel_sha256']:
            raise InstallError('installer_boot_profile_custody')

    def __call__(self,root,plan,uuid):
        self.system.require_root();root=Path(root)
        operation=plan['options']['operation_id']
        if not re.fullmatch('[0-9a-f]{32}',operation):raise InstallError('installer_boot_operation')
        runtime,archive=machinery()
        kernel=root/'boot'/('vmlinuz-'+RELEASE)
        if kernel.is_symlink() or runtime.digest(kernel)!=self.profile['kernel_sha256']:
            raise InstallError('installer_boot_kernel_changed')
        base=root/'tmp'/('toddy-installed-boot-'+operation)
        if base.parent.resolve()!=base.parent or base.exists() or base.is_symlink():raise InstallError('installer_boot_stage_not_fresh')
        # H10 reads source-owned package records and actual target ELF dependencies;
        # it verifies native bytes before staging and never reads host /etc/home.
        base.mkdir(mode=0o700)
        stage=base/'runtime'
        records=self.bundle/'records'
        try:
            runtime.stage_runtime(root,stage,records)
            owners=runtime.installed_records(root,records)
            def copy_owned(virtual):
                source,canonical=runtime.target_resolve(root,virtual)
                if canonical not in owners or not source.is_file() or source.is_symlink() or runtime.digest(source)!=owners[canonical][3]['sha256']:
                    raise InstallError('installer_boot_unowned_runtime')
                destination=stage/runtime.destination_path(virtual)
                destination.parent.mkdir(parents=True,exist_ok=True)
                if destination.exists():
                    if runtime.digest(destination)!=runtime.digest(source):raise InstallError('installer_boot_alias_collision')
                else:
                    shutil.copyfile(source,destination);destination.chmod(stat.S_IMODE(source.stat().st_mode)&0o777)
            for program in TOOLS:
                copy_owned(program)
                for dependency in runtime.runtime_dependencies(root,program):copy_owned(dependency)
            for virtual,expected in sorted(self.module_entries.items()):
                source=root/virtual.lstrip('/');destination=stage/virtual.lstrip('/');info=source.lstat()
                if {'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid} != {key:expected[key] for key in ('mode','uid','gid')} or source.is_symlink() or os.listxattr(source):
                    raise InstallError('installer_boot_module_metadata_changed')
                if expected.get('directory'):
                    destination.mkdir(parents=True,exist_ok=True);destination.chmod(stat.S_IMODE(info.st_mode))
                elif expected.get('sha256') and stat.S_ISREG(info.st_mode) and runtime.digest(source)==expected['sha256']:
                    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination);destination.chmod(stat.S_IMODE(info.st_mode)&0o777)
                else:raise InstallError('installer_boot_module_bytes_changed')
            for name in self.profile['modules']:
                # Real native depmod indices must resolve each selected name, whether
                # builtin or an exact packaged module, before archive construction.
                output=self.system.run(['/usr/sbin/chroot',str(root),'/usr/sbin/modprobe','--show-depends','-S',RELEASE,name])
                for line in output.splitlines():
                    if line.startswith('builtin '):continue
                    if not re.fullmatch(r'insmod /(?:usr/)?lib/modules/7\.1\.8-toddy/[A-Za-z0-9_./+-]+\.ko(?:\.(?:xz|zst|gz))?',line):
                        raise InstallError('installer_boot_module_dependency_unreviewed')
                    virtual=line.split(' ',1)[1];canonical='/usr/lib/modules/'+virtual.split('/lib/modules/',1)[1]
                    if canonical not in self.module_entries:raise InstallError('installer_boot_module_dependency_missing')
            (stage/'init').write_bytes(init_script(uuid,self.profile['modules']));(stage/'init').chmod(0o755)
            expected=archive.inventory(stage,self.profile['epoch'])
            names=b'\0'.join(name.encode() for name in sorted(expected))+b'\0'
            for tool in ('/usr/bin/bsdcpio','/usr/bin/gzip'):
                source,canonical=runtime.target_resolve(root,tool)
                if canonical not in owners or runtime.digest(source)!=owners[canonical][3]['sha256']:raise InstallError('installer_boot_archive_tool_changed')
            rawpath=base/'initramfs.cpio'
            prefix=['/usr/sbin/chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C']
            with rawpath.open('xb') as stream:
                subprocess.run(prefix+['/bin/bash','-c','cd "$1" && exec bsdcpio -o --null --format=newc --owner 0:0 --quiet','archive','/'+stage.relative_to(root).as_posix()],input=names,stdout=stream,stderr=subprocess.DEVNULL,check=True,timeout=120,close_fds=True,env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C'})
            raw=rawpath.read_bytes();archive.validate_newc(raw,expected,self.profile['epoch'])
            compressed=base/'initramfs.cpio.gz'
            with compressed.open('xb') as stream:
                subprocess.run(prefix+['/usr/bin/gzip','-n','-9','-c','/'+rawpath.relative_to(root).as_posix()],stdout=stream,stderr=subprocess.DEVNULL,check=True,timeout=120,close_fds=True,env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C'})
            data=compressed.read_bytes()
            if gzip.decompress(data)!=raw:raise InstallError('installer_boot_archive_roundtrip')
            name='initramfs-'+RELEASE+'-installed.img';target=root/'boot'/name
            if target.exists() or target.is_symlink() or target.parent.resolve()!=target.parent:raise InstallError('installer_boot_output_exists')
            with target.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
            target.chmod(0o644)
            return {'verified':True,'kernel':kernel.name,'initramfs':name,'kernel_sha256':runtime.digest(kernel),'initramfs_sha256':runtime.digest(target)}
        finally:
            # Only this exclusive, source-created staging tree is removable. Native
            # failures are not retried, and existing boot artifacts are preserved.
            if base.is_dir() and not base.is_symlink():shutil.rmtree(base)
