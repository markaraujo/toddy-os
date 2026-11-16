"""Host-only command-plan fixtures. No block device is formatted or mounted.

The fake native runner proves dispatch/guards and private-file hygiene behavior,
never a real installation, filesystem/GRUB success or detached-media boot.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest

from runtime.installer.backend import Installer, Journal
from runtime.installer.disk_plan import (InstallError, ProductionPolicy,
    QualificationPolicy, make_plan, partition_script, validate_plan)
from runtime.installer.installed_identity import audit_hygiene, write_identity, create_owner
from runtime.installer.linux_disk import LinuxDisk


def inputs():
    disk = {'path': '/dev/fixture-disk', 'major_minor': '253:16', 'serial': 'TODDY-INSTALL-FIXTURE',
        'size': 16 * 1024**3, 'sector_size': 512, 'model': 'QEMU HARDDISK', 'driver': 'virtio_blk',
        'readonly': False, 'mounted': False, 'blank': True, 'virtual': True}
    options = {'operation_id': 'a' * 32, 'boot_mode': 'uefi', 'username': 'owner',
        'uid': os.getuid() if os.getuid() >= 1000 else 1000,
        'gid': os.getgid() if os.getgid() >= 100 else 1000,
        'locale': 'pt_BR.UTF-8', 'timezone': 'UTC',
        'hostname': 'toddy-owner', 'ai_choice': 'later', 'extras': ['vscode', 'docker']}
    payload = {'sha256': 'b' * 64, 'catalog_sha256': 'c' * 64, 'bytes': 2 * 1024**3}
    return disk, options, payload


class FakeNative:
    """Only records commands and simulates local target account fixture files."""
    def __init__(self, disk):
        self.disk = copy.deepcopy(disk)
        self.calls = []
        self.fail = None
        self.after_partition = None
    def require_root(self):
        pass
    def preflight(self, firmware):
        pass
    def probe(self, path):
        return copy.deepcopy(self.disk)
    def partition(self, disk, number):
        return '/dev/fixture-part' + str(number)
    def verify_partition_table(self, plan):
        return None
    def verify_mount(self, device, target, filesystem):
        return None
    def filesystem_uuid(self, path):
        return 'ABCD-1234' if path.endswith('1') else '11111111-1111-1111-1111-111111111111'
    def run(self, arguments, *, data=None, timeout=30):
        self.calls.append((list(arguments), data))
        if self.fail and any(self.fail in arg for arg in arguments):
            raise InstallError('injected_native_failure')
        if arguments[0].endswith('/sfdisk') and self.after_partition:
            self.after_partition()
        if '/usr/sbin/useradd' in arguments:
            root = Path(arguments[1])
            username = arguments[-1]
            uid = arguments[arguments.index('--uid') + 1]
            gid = arguments[arguments.index('--gid') + 1]
            with (root / 'etc/passwd').open('a') as stream:
                stream.write(f'{username}:x:{uid}:{gid}::/home/{username}:/bin/bash\n')
            if '--groups' in arguments and arguments[arguments.index('--groups')+1]=='wheel':
                group=root/'etc/group';group.write_text(group.read_text().replace('wheel:x:97:\n','wheel:x:97:'+username+'\n'))
            (root / 'home' / username).mkdir(parents=True)
            if os.geteuid() == 0:
                os.chown(root / 'home' / username, int(uid), int(gid))
        return ''


class DiskPlanTests(unittest.TestCase):
    def test_explicit_aligned_uefi_and_bios_extents_and_frozen_digest(self):
        disk, options, payload = inputs()
        for firmware in ('uefi', 'bios'):
            for sector in (512, 4096):
                with self.subTest(firmware=firmware, sector=sector):
                    disk['sector_size'] = sector
                    options['boot_mode'] = firmware
                    plan = make_plan(disk, options, payload)
                    self.assertEqual(validate_plan(plan), plan)
                    self.assertEqual(plan['partitions'][0]['kind'], 'esp' if firmware == 'uefi' else 'bios')
                    for partition in plan['partitions']:
                        self.assertEqual(partition['start'] * sector % 1024**2, 0)
                    self.assertIn('label: gpt', partition_script(plan))
                    changed = copy.deepcopy(plan)
                    changed['partitions'][1]['sectors'] -= 1
                    with self.assertRaises(InstallError):
                        validate_plan(changed)

    def test_invalid_device_state_choices_secret_fields_and_space_fail_closed(self):
        disk, options, payload = inputs()
        for change in ({'mounted': True}, {'blank': False}, {'readonly': True}, {'serial': ''}):
            with self.assertRaises(InstallError):
                make_plan(dict(disk, **change), options, payload)
        for change in ({'password': 'must-not-enter-plan'}, {'username': '../owner'}, {'username':'tester'}, {'gid':100},
                       {'uid': True}, {'timezone': '../etc/passwd'}, {'extras': ['mise']}, {'extras': ['docker', 'docker']}):
            with self.assertRaises(InstallError):
                make_plan(disk, dict(options, **change), payload)
        with self.assertRaisesRegex(InstallError, 'insufficient'):
            make_plan(disk, options, dict(payload, bytes=15 * 1024**3))

    def test_qualification_policy_is_separate_from_production_physical_support(self):
        disk, _, _ = inputs()
        physical = dict(disk, virtual=False, model='owner selected physical disk', driver='nvme', serial='OWNER-PHYSICAL-EXAMPLE')
        ProductionPolicy().check(physical)  # pure validation, zero device access
        with self.assertRaises(InstallError):
            QualificationPolicy(disk['serial']).check(physical)

    def test_real_probe_refuses_a_regular_file_without_device_mutation(self):
        with tempfile.NamedTemporaryFile() as source:
            with self.assertRaisesRegex(InstallError, 'not_block_device'):
                LinuxDisk().probe(source.name)


class InstallerBackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        disk, options, payload = inputs()
        self.plan = make_plan(disk, options, payload)
        self.system = FakeNative(disk)
        self.journal = Journal(self.root / 'journal')
        self.installer = Installer(self.journal, policy=QualificationPolicy(disk['serial']),
            verify_payload=self.receipt, install_payload=self.payload, build_boot=self.boot,
            save_pending=self.pending, system=self.system, mount_base=self.root / 'mounts')
        self.read_fd, write_fd = os.pipe()
        os.write(write_fd, b'fixture-only-password-1234')
        os.close(write_fd)

    def tearDown(self):
        os.close(self.read_fd)
        self.journal.close()
        self.temp.cleanup()

    def receipt(self, plan):
        return {'verified': True, 'payload_sha256': plan['payload']['sha256'],
                'catalog_sha256': plan['payload']['catalog_sha256']}

    def payload(self, target, plan):
        for folder in ('etc', 'usr/share/zoneinfo', 'boot', 'home'):
            (target / folder).mkdir(parents=True, exist_ok=True)
        (target / 'etc/passwd').write_text('root:x:0:0:root:/root:/bin/bash\n')
        (target / 'etc/group').write_text('root:x:0:\nwheel:x:97:\n')
        (target / 'usr/share/zoneinfo/UTC').write_bytes(b'fixture timezone bytes')
        (target / 'etc/machine-id').write_bytes(b'')
        (target / 'etc/localtime').symlink_to('../usr/share/zoneinfo/UTC')
        (target / 'etc/toddy').mkdir()
        (target / 'etc/toddy/grub.cfg').write_text('# Accepted foundation fixture reference; not a new boot proof.\n')
        (target / 'boot/grub').mkdir()
        (target / 'boot/grub/grub.cfg').symlink_to('../../etc/toddy/grub.cfg')
        return self.receipt(plan)

    def boot(self, target, plan, root_uuid):
        values = {'verified': True, 'kernel': 'vmlinuz-fixture', 'initramfs': 'initramfs-fixture.img'}
        for kind in ('kernel', 'initramfs'):
            data = (kind + '-fixture-bytes').encode()
            (target / 'boot' / values[kind]).write_bytes(data)
            values[kind + '_sha256'] = hashlib.sha256(data).hexdigest()
        return values

    def pending(self, target, plan):
        path = target / 'home/owner/.local/state/toddy/setup/pending.json'
        path.parent.mkdir(parents=True, mode=0o700)
        data = b'host-fixture-only-shared-writer-is-integrated-by-calamares'
        path.write_bytes(data)
        path.chmod(0o600)
        if os.geteuid() == 0:
            os.chown(path.parent, plan['options']['uid'], plan['options']['gid'])
            os.chown(path, plan['options']['uid'], plan['options']['gid'])
        return {'verified': True, 'uid': plan['options']['uid'], 'mode': 0o600,
            'path': '/home/owner/.local/state/toddy/setup/pending.json',
            'catalog_sha256': plan['payload']['catalog_sha256'], 'manifest_sha256': hashlib.sha256(data).hexdigest()}

    def execute(self, **kwargs):
        values = {'confirmation': self.plan['plan_sha256'], 'authorize': lambda _: True, 'credential_fd': self.read_fd}
        values.update(kwargs)
        return self.installer.execute(self.plan, **values)

    def target(self):
        return self.root / 'mounts' / ('target-' + self.plan['options']['operation_id'])

    def test_default_is_review_only_and_cancellation_before_write_dispatches_nothing(self):
        result = self.installer.execute(self.plan)
        self.assertFalse(result['disk_writes'])
        self.assertEqual(self.system.calls, [])
        canceled = threading.Event()
        canceled.set()
        result = self.execute(cancel=canceled)
        self.assertEqual(result['state'], 'canceled-before-write')
        self.assertFalse(result['disk_writes'])
        self.assertEqual(self.system.calls, [])

    def test_confirmation_identity_revocation_and_payload_preflight_prevent_writes(self):
        with self.assertRaisesRegex(InstallError, 'confirmation'):
            self.execute(confirmation='0' * 64)
        with self.assertRaisesRegex(InstallError, 'authorization'):
            self.execute(authorize=lambda _: False)
        self.system.disk['serial'] = 'TODDY-INSTALL-CHANGED'
        with self.assertRaises(InstallError):
            self.execute()
        self.assertEqual(self.system.calls, [])

    def test_unqualified_composed_payload_cannot_reach_partitioner(self):
        self.installer.verify_payload = lambda _: {'verified': True}
        with self.assertRaisesRegex(InstallError, 'composed_payload'):
            self.execute()
        self.assertEqual(self.system.calls, [])

    def test_command_fixture_full_handoff_fstab_hygiene_and_safe_boot_menu(self):
        result = self.execute()
        self.assertEqual(result['state'], 'completed')
        self.assertEqual(result['installed_boot_validation'], 'pending')
        commands = [arguments for arguments, _ in self.system.calls]
        self.assertTrue(any(arguments[0].endswith('/sfdisk') for arguments in commands))
        self.assertTrue(any(arguments[0].endswith('/mkfs.ext4') for arguments in commands))
        self.assertTrue(any('--target=x86_64-efi' in arguments for arguments in commands))
        self.assertFalse(any('--force' in arguments or ('-F' in arguments and arguments[0].endswith('/mkfs.ext4')) for arguments in commands))
        fstab = (self.target() / 'etc/fstab').read_text()
        self.assertIn('UUID=11111111-1111-1111-1111-111111111111 / ext4', fstab)
        self.assertIn('UUID=ABCD-1234 /boot/efi vfat', fstab)
        self.assertNotIn('/dev/fixture', fstab)
        grub = (self.target() / 'boot/grub/grub.cfg').read_text()
        self.assertTrue((self.target() / 'boot/grub/grub.cfg').is_symlink())
        self.assertEqual(os.readlink(self.target() / 'boot/grub/grub.cfg'), '../../etc/toddy/grub.cfg')
        self.assertIn('Accepted foundation fixture', (self.target() / 'usr/share/toddy/recovery/foundation-grub.cfg').read_text())
        self.assertFalse((self.target() / 'etc/localtime').is_symlink())
        self.assertEqual((self.target() / 'usr/share/zoneinfo/UTC').read_bytes(), b'fixture timezone bytes')
        self.assertIn('Toddy text recovery', grub)
        self.assertIn('systemd.unit=multi-user.target', grub)
        self.assertNotIn('live', grub)
        self.assertEqual((self.target() / 'etc/machine-id').read_bytes(), b'')
        dump = '\n'.join(self.journal.db.iterdump())
        self.assertNotIn('fixture-only-password', dump)
        self.assertIn('kernel_sha256', dump)
        before = len(self.system.calls)
        replay = self.execute()
        self.assertFalse(replay['replayed'])
        self.assertEqual(before, len(self.system.calls))

    def test_bios_handoff_preserves_canonical_config_without_creating_esp(self):
        disk, options, content = inputs()
        options['boot_mode'] = 'bios'
        self.plan = make_plan(disk, options, content)
        result = self.execute()
        self.assertEqual(result['boot_mode'], 'bios')
        self.assertTrue(any('--target=i386-pc' in arguments for arguments, _ in self.system.calls))
        self.assertFalse(any(arguments[0].endswith('/mkfs.fat') for arguments, _ in self.system.calls))
        self.assertNotIn('/boot/efi', (self.target() / 'etc/fstab').read_text())
        self.assertTrue((self.target() / 'boot/grub/grub.cfg').is_symlink())

    def test_unknown_timezone_and_grub_links_are_refused_without_following(self):
        target = self.root / 'unknown-links'
        target.mkdir()
        self.payload(target, self.plan)
        localtime = target / 'etc/localtime'
        localtime.unlink()
        localtime.symlink_to('/etc/passwd')
        with self.assertRaisesRegex(InstallError, 'identity_symlink'):
            write_identity(target, self.plan, root_uuid='1111-1111', esp_uuid='ABCD-1234')
        self.assertEqual(os.readlink(localtime), '/etc/passwd')
        grub = target / 'boot/grub/grub.cfg'
        grub.unlink()
        grub.symlink_to('/etc/shadow')
        boot = self.boot(target, self.plan, '1111-1111')
        with self.assertRaisesRegex(InstallError, 'link_not_canonical'):
            self.installer._grub(target, self.plan, boot, '1111-1111')
        self.assertEqual(self.system.calls, [])

    def test_failure_after_partition_is_uncertain_and_not_replayed(self):
        self.system.fail = 'mkfs.ext4'
        with self.assertRaisesRegex(InstallError, 'injected'):
            self.execute()
        self.assertEqual(self.journal.snapshot('a' * 32)['state'], 'needs-reconciliation')
        count = len(self.system.calls)
        with self.assertRaisesRegex(InstallError, 'requires_reconciliation'):
            self.execute()
        self.assertEqual(len(self.system.calls), count)

    def test_cancel_after_first_write_stops_at_boundary_without_killing_commit(self):
        canceled = threading.Event()
        self.system.after_partition = canceled.set
        with self.assertRaisesRegex(InstallError, 'safe_boundary_rescue_required'):
            self.execute(cancel=canceled)
        self.assertFalse(any('mkfs' in args[0] for args, _ in self.system.calls))
        self.assertEqual(self.journal.snapshot('a' * 32)['state'], 'needs-reconciliation')

    def test_one_writer_lock_prevents_any_native_command(self):
        fd = os.open(self.journal.directory / 'writer.lock', os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(InstallError, 'writer_busy'):
                self.execute()
            self.assertEqual(self.system.calls, [])
        finally:
            os.close(fd)

    def test_identity_and_live_private_state_are_rejected_not_silently_sanitized(self):
        target = self.root / 'identity-fixture'
        target.mkdir()
        self.payload(target, self.plan)
        (target / 'etc/machine-id').write_text('inherited-builder-id')
        with self.assertRaisesRegex(InstallError, 'inherited_machine_id'):
            write_identity(target, self.plan, root_uuid='1111-1111', esp_uuid='ABCD-1234')
        self.assertEqual((target / 'etc/machine-id').read_text(), 'inherited-builder-id')
        (target / 'etc/machine-id').write_bytes(b'')
        (target / 'root/.ssh').mkdir(parents=True)
        with self.assertRaisesRegex(InstallError, 'private_or_live'):
            audit_hygiene(target, self.plan)

    def test_missing_native_admin_group_refuses_owner_creation_before_account_commands(self):
        target=self.root/'missing-admin-group';target.mkdir();self.payload(target,self.plan)
        (target/'etc/group').unlink()
        with self.assertRaisesRegex(InstallError,'admin_group_missing'):
            create_owner(target,self.plan,self.read_fd,self.system)
        self.assertEqual(self.system.calls,[])

    def test_actual_executor_state_path_is_rejected_from_fresh_image(self):
        target=self.root/'inherited-executor';target.mkdir();self.payload(target,self.plan)
        (target/'var/lib/toddy/executor').mkdir(parents=True)
        with self.assertRaisesRegex(InstallError,'private_or_live'):
            audit_hygiene(target,self.plan)


if __name__ == '__main__':
    unittest.main()
