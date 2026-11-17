"""Read-only Linux block identity and native shell-free installer operations."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

from .disk_plan import InstallError, validate_disk


class LinuxDisk:
    def run(self, arguments, *, data=None, timeout=30):
        # Callers pass fixed native argv and reviewed values, never a shell.
        # Input can contain login secrets; no command/output/body is logged here.
        result = subprocess.run(arguments, input=data, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=timeout, check=False,
            env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'}, close_fds=True)
        if result.returncode:
            raise InstallError('installer_native_command_failed')
        if len(result.stdout) > 2 * 1024 * 1024:
            raise InstallError('installer_native_output_limit')
        return result.stdout.decode('utf-8', errors='strict').strip()

    def require_root(self):
        if os.geteuid() != 0:
            raise InstallError('installer_root_required')

    def preflight(self, firmware):
        programs = ['/usr/sbin/sfdisk', '/usr/sbin/mkfs.ext4', '/usr/sbin/blkid',
            '/usr/bin/mount', '/usr/bin/umount', '/usr/bin/findmnt', '/usr/sbin/chroot',
            '/usr/bin/lsblk', '/usr/sbin/wipefs', '/usr/bin/sync']
        if firmware == 'uefi':
            programs.append('/usr/sbin/mkfs.fat')
        if any(not os.path.isfile(path) or not os.access(path, os.X_OK) for path in programs):
            raise InstallError('installer_required_native_tool_unavailable')

    def probe(self, device, *, require_blank=True):
        try:
            path = Path(device).resolve(strict=True)
            metadata = path.stat()
            if not stat.S_ISBLK(metadata.st_mode):
                raise InstallError('installer_target_not_block_device')
            # Kernel exclusive-open refusal also catches mounted use outside this
            # process's mount namespace. This probe is read-only, never a lock
            # substitute for final identity/authorization or the single writer.
            exclusive = os.open(path, os.O_RDONLY | os.O_EXCL | os.O_NONBLOCK)
            os.close(exclusive)
            actual = '{}:{}'.format(os.major(metadata.st_rdev), os.minor(metadata.st_rdev))
            sysfs = (Path('/sys/dev/block') / actual).resolve(strict=True)
            if (sysfs / 'partition').exists() or any((sysfs / 'holders').iterdir()):
                raise InstallError('installer_target_partition_or_held')
            raw = json.loads(self.run(['/usr/bin/lsblk', '--json', '--bytes', '--paths', '--output',
                'PATH,MAJ:MIN,SERIAL,SIZE,LOG-SEC,MODEL,RO,TYPE,MOUNTPOINTS', str(path)]))
            devices = raw['blockdevices']
            if len(devices) != 1:
                raise InstallError('installer_disk_ambiguous')
            row = devices[0]
            if row['type'] != 'disk' or row['maj:min'] != actual or row['path'] != str(path):
                raise InstallError('installer_disk_identity')
            def mounted(node):
                return any(node.get('mountpoints') or []) or any(mounted(child) for child in node.get('children', []))
            signatures = json.loads(self.run(['/usr/sbin/wipefs', '--no-act', '--json', str(path)]))
            driver_path = sysfs / 'device/driver'
            driver = driver_path.resolve().name if driver_path.exists() else ''
            model = (row.get('model') or '').strip()
            virtual = driver == 'virtio_blk' or 'QEMU' in model.upper()
            disk = {'path': str(path), 'major_minor': actual, 'serial': (row.get('serial') or '').strip(),
                'size': int(row['size']), 'sector_size': int(row['log-sec']), 'model': model,
                'driver': driver, 'readonly': bool(row['ro']), 'mounted': bool(mounted(row)),
                'blank': not signatures.get('signatures') and not row.get('children'), 'virtual': virtual}
            validate_disk(disk, require_blank=require_blank)
            return disk
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise InstallError('installer_disk_probe_failed') from exc

    def partition(self, disk, number):
        """Resolve an observed kernel child, not a guessed /dev/vdX suffix."""
        sysfs = (Path('/sys/dev/block') / disk['major_minor']).resolve(strict=True)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            for candidate in sysfs.iterdir():
                marker = candidate / 'partition'
                if marker.is_file() and marker.read_text().strip() == str(number):
                    path = Path('/dev') / candidate.name
                    if path.exists():
                        metadata = path.stat()
                        major_minor = '{}:{}'.format(os.major(metadata.st_rdev), os.minor(metadata.st_rdev))
                        if not stat.S_ISBLK(metadata.st_mode) or major_minor != (candidate / 'dev').read_text().strip():
                            raise InstallError('installer_partition_identity')
                        return str(path)
            time.sleep(.05)
        raise InstallError('installer_partition_not_ready')

    def filesystem_uuid(self, path):
        value = self.run(['/usr/sbin/blkid', '--match-tag', 'UUID', '--output', 'value', path])
        if not re.fullmatch('[A-Fa-f0-9-]{4,40}', value):
            raise InstallError('installer_filesystem_uuid')
        return value

    def verify_partition_table(self, plan):
        table = json.loads(self.run(['/usr/sbin/sfdisk', '--json', plan['target']['path']]))['partitiontable']
        if table.get('label') != 'gpt' or table.get('sectorsize') != plan['target']['sector_size'] or len(table.get('partitions', [])) != 2:
            raise InstallError('installer_partition_postcondition')
        for actual, expected in zip(table['partitions'], plan['partitions']):
            if actual.get('start') != expected['start'] or actual.get('size') != expected['sectors'] or actual.get('type', '').upper() != expected['type']:
                raise InstallError('installer_partition_postcondition')

    def verify_mount(self, device, target, filesystem):
        document = json.loads(self.run(['/usr/bin/findmnt', '--json', '--target', str(target),
            '--output', 'TARGET,FSTYPE,MAJ:MIN']))
        metadata = Path(device).stat()
        major_minor = '{}:{}'.format(os.major(metadata.st_rdev), os.minor(metadata.st_rdev))
        rows = document.get('filesystems', [])
        if len(rows) != 1 or rows[0].get('target') != str(target) or rows[0].get('fstype') != filesystem or rows[0].get('maj:min') != major_minor:
            raise InstallError('installer_mount_postcondition')
