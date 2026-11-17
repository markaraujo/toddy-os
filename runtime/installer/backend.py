"""Calamares-facing native installation engine with an exact destructive boundary.

Default execution is plan-only. A real run needs reviewed digest confirmation,
current destructive owner authorization, designated policy, verified composed
payload/boot/shared-setup handoffs and root. This module is never run at import.
"""
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import sqlite3
import stat

from .disk_plan import InstallError, validate_plan, partition_script
from .installed_identity import regular, write_identity, create_owner, audit_hygiene
from .linux_disk import LinuxDisk


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = self.directory.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise InstallError('installer_journal_private_directory')
        path = self.directory / 'operations.sqlite'
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid() or metadata.st_nlink != 1 or stat.S_IMODE(metadata.st_mode) != 0o600:
                raise InstallError('installer_journal_private_file')
        finally:
            os.close(fd)
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,plan_sha256 TEXT NOT NULL,state TEXT NOT NULL,step TEXT NOT NULL,cancel INTEGER NOT NULL DEFAULT 0)')
        self.db.execute('CREATE TABLE IF NOT EXISTS receipts(operation_id TEXT NOT NULL,step TEXT NOT NULL,body TEXT NOT NULL,PRIMARY KEY(operation_id,step))')

    def close(self):
        self.db.close()

    def request_cancel(self, operation_id):
        self.db.execute('UPDATE operations SET cancel=1 WHERE id=?', (operation_id,))

    def snapshot(self, operation_id):
        cursor = self.db.execute('SELECT id,plan_sha256,state,step,cancel FROM operations WHERE id=?', (operation_id,))
        row = cursor.fetchone()
        return dict(zip([c[0] for c in cursor.description], row)) if row else None


class Installer:
    """One engine/writer; native tools execute only after explicit confirmation.

    The trusted Calamares integration supplies these callbacks:
      verify_payload(plan): verify actual offline closure/media/catalog, no write;
      install_payload(root, plan): own archives/native package closure, not a
          dirty builder root copy; return verified + payload/catalog SHA bindings;
      build_boot(root, plan, root_uuid): verified installed initramfs and accepted
          kernel, returning kernel/initramfs relative leaf names + SHA-256 hashes;
      save_pending(root, plan): invoke the shared PendingStore as installed user,
          return verified, uid, mode, path, catalog_sha256 and manifest_sha256.
    Callbacks and policy are installed code bindings, never plan-supplied scripts.
    """
    def __init__(self, journal, *, policy, verify_payload, install_payload, build_boot,
                 save_pending, system=None, mount_base='/run/toddy-installer'):
        self.journal = journal
        self.policy = policy
        self.verify_payload = verify_payload
        self.install_payload = install_payload
        self.build_boot = build_boot
        self.save_pending = save_pending
        self.system = system if system is not None else LinuxDisk()
        self.mount_base = Path(mount_base)

    def execute(self, candidate, *, confirmation=None, authorize=None, credential_fd=None, cancel=None):
        plan = validate_plan(candidate)
        if confirmation is None:
            return {'state': 'review_required', 'plan': plan, 'disk_writes': False}
        if confirmation != plan['plan_sha256']:
            raise InstallError('installer_confirmation_mismatch')
        if not callable(authorize) or not authorize(copy.deepcopy(plan)):
            raise InstallError('installer_current_destructive_authorization_required')
        self.system.require_root()
        self.system.preflight(plan['options']['boot_mode'])
        if type(credential_fd) is not int or not stat.S_ISFIFO(os.fstat(credential_fd).st_mode):
            raise InstallError('installer_private_login_pipe_required')
        self.policy.check(plan['target'])
        # Required composed inputs must be qualified before a disk write.
        self._payload_receipt(self.verify_payload(copy.deepcopy(plan)), plan)
        lock_fd = os.open(self.journal.directory / 'writer.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        mounts = []
        cleanup_attempted = False
        operation_id = plan['options']['operation_id']
        try:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise InstallError('installer_writer_busy') from exc
            previous = self.journal.snapshot(operation_id)
            if previous:
                if previous['plan_sha256'] != plan['plan_sha256']:
                    raise InstallError('installer_operation_identity_conflict')
                if previous['state'] == 'completed':
                    return {'state': 'completed', 'operation_id': operation_id, 'replayed': False}
                # A prior callback/native command may already have changed disk.
                # Reconcile observed postconditions from the rescue medium first.
                raise InstallError('installer_previous_outcome_requires_reconciliation')
            self.journal.db.execute('INSERT INTO operations(id,plan_sha256,state,step) VALUES(?,?,?,?)',
                (operation_id, plan['plan_sha256'], 'prepared', 'preflight'))
            if self._canceled(operation_id, cancel):
                self._state(operation_id, 'canceled-before-write', 'preflight')
                return {'state': 'canceled-before-write', 'disk_writes': False}
            # Reserve a private usable target path before touching the disk.
            for parent in (self.mount_base, *self.mount_base.parents):
                if parent.is_symlink():
                    raise InstallError('installer_mount_base_not_private')
            self.mount_base.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self.mount_base.stat().st_uid != os.geteuid() or self.mount_base.stat().st_mode & 0o077:
                raise InstallError('installer_mount_base_not_private')
            target = self.mount_base / ('target-' + operation_id)
            target.mkdir(mode=0o700)
            current = self.system.probe(plan['target']['path'])
            self.policy.check(current)
            if current != plan['target']:
                raise InstallError('installer_target_changed_since_review')
            # Current exact-disk confirmation is checked again at the first write.
            if not authorize(copy.deepcopy(plan)):
                raise InstallError('installer_current_destructive_authorization_required')
            if self._canceled(operation_id, cancel):
                self._state(operation_id, 'canceled-before-write', 'preflight')
                return {'state': 'canceled-before-write', 'disk_writes': False}
            self._step(operation_id, 'partition-table', lambda: self.system.run(
                ['/usr/sbin/sfdisk', '--wipe', 'never', '--wipe-partitions', 'never', plan['target']['path']],
                data=partition_script(plan).encode()))
            self._step(operation_id, 'partition-postcondition', lambda: self.system.verify_partition_table(plan))
            self._boundary(operation_id, cancel)
            # Kernel child identities are observed after sfdisk, not guessed.
            root_device = self.system.partition(plan['target'], 2)
            boot_device = self.system.partition(plan['target'], 1)
            self._step(operation_id, 'root-filesystem', lambda: self.system.run(
                ['/usr/sbin/mkfs.ext4', '-L', 'ToddyRoot', root_device], timeout=180))
            self._boundary(operation_id, cancel)
            esp = None
            if plan['options']['boot_mode'] == 'uefi':
                self._step(operation_id, 'esp-filesystem', lambda: self.system.run(
                    ['/usr/sbin/mkfs.fat', '-F', '32', '-n', 'TODDYESP', boot_device]))
                esp = self.system.filesystem_uuid(boot_device)
            root_uuid = self.system.filesystem_uuid(root_device)
            self._receipt(operation_id, 'filesystems', {'root_uuid': root_uuid, 'esp_uuid': esp})
            def mount_root():
                self.system.run(['/usr/bin/mount', '-t', 'ext4', root_device, str(target)])
                mounts.append(target)
                self.system.verify_mount(root_device, target, 'ext4')
                self.system.run(['/usr/bin/mount', '--make-private', str(target)])
            self._step(operation_id, 'mount-target', mount_root)
            self._boundary(operation_id, cancel)
            self._step(operation_id, 'composed-payload', lambda: self._payload_receipt(self.install_payload(target, copy.deepcopy(plan)), plan))
            self._boundary(operation_id, cancel)
            if esp is not None:
                if (target / 'boot').is_symlink():
                    raise InstallError('installer_target_boot_symlink')
                esp_path = target / 'boot/efi'
                esp_path.mkdir(parents=True, exist_ok=True)
                if esp_path.is_symlink():
                    raise InstallError('installer_target_esp_symlink')
                self._step(operation_id, 'mount-esp', lambda: self._mount(boot_device, esp_path, mounts, 'vfat'))
            self._step(operation_id, 'installed-identity', lambda: write_identity(target, plan, root_uuid=root_uuid, esp_uuid=esp))
            self._boundary(operation_id, cancel)
            self._runtime_mounts(target, plan, root_device, boot_device, mounts, operation_id)
            self._step(operation_id, 'fresh-owner-login', lambda: create_owner(target, plan, credential_fd, self.system))
            self._boundary(operation_id, cancel)
            boot = self._step(operation_id, 'installed-initramfs', lambda: self.build_boot(target, copy.deepcopy(plan), root_uuid))
            self._boot_receipt(target, boot)
            self._receipt(operation_id, 'boot', boot)
            grub_receipt = self._step(operation_id, 'grub', lambda: self._grub(target, plan, boot, root_uuid))
            self._receipt(operation_id, 'grub', grub_receipt)
            self._boundary(operation_id, cancel)
            self._step(operation_id, 'installed-hygiene', lambda: audit_hygiene(target, plan))
            self._step(operation_id, 'deferred-setup-handoff', lambda: self._pending_receipt(target, self.save_pending(target, copy.deepcopy(plan)), plan))
            self._step(operation_id, 'sync-installed-state', lambda: self.system.run(['/usr/bin/sync', '-f', str(target)]))
            # Completion is recorded only after every owned mount is released.
            cleanup_attempted = True
            self._unmount(mounts)
            self._state(operation_id, 'completed', 'complete')
            return {'state': 'completed', 'operation_id': operation_id, 'root_uuid': root_uuid,
                    'boot_mode': plan['options']['boot_mode'], 'installed_boot_validation': 'pending'}
        except BaseException:
            state = self.journal.snapshot(operation_id)
            if state and state['state'] not in ('canceled-before-write', 'completed'):
                self._state(operation_id, 'needs-reconciliation', state['step'])
            raise
        finally:
            try:
                if not cleanup_attempted:
                    self._unmount(mounts)
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)

    def _payload_receipt(self, receipt, plan):
        if not isinstance(receipt, dict) or receipt != {'verified': True, 'payload_sha256': plan['payload']['sha256'], 'catalog_sha256': plan['payload']['catalog_sha256']}:
            raise InstallError('installer_composed_payload_not_verified')

    def _pending_receipt(self, root, receipt, plan):
        import hashlib
        expected = {'verified': True, 'uid': plan['options']['uid'], 'mode': 0o600,
            'path': '/home/' + plan['options']['username'] + '/.local/state/toddy/setup/pending.json',
            'catalog_sha256': plan['payload']['catalog_sha256']}
        if not isinstance(receipt, dict) or set(receipt) != set(expected) | {'manifest_sha256'} or any(receipt[key] != value for key, value in expected.items()):
            raise InstallError('installer_pending_handoff_not_verified')
        path = root
        for part in Path(expected['path']).parts[1:]:
            path /= part
            if path.is_symlink():
                raise InstallError('installer_pending_handoff_symlink')
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_uid != expected['uid'] or stat.S_IMODE(metadata.st_mode) != expected['mode'] or metadata.st_size > 65536 or hashlib.sha256(path.read_bytes()).hexdigest() != receipt['manifest_sha256']:
            raise InstallError('installer_pending_handoff_postcondition')
        directory = path.parent.stat()
        if directory.st_uid != expected['uid'] or stat.S_IMODE(directory.st_mode) != 0o700:
            raise InstallError('installer_pending_handoff_postcondition')

    def _boot_receipt(self, root, receipt):
        if not isinstance(receipt, dict) or set(receipt) != {'verified', 'kernel', 'initramfs', 'kernel_sha256', 'initramfs_sha256'} or receipt['verified'] is not True:
            raise InstallError('installer_boot_not_verified')
        import hashlib
        for kind in ('kernel', 'initramfs'):
            leaf = receipt[kind]
            if not isinstance(leaf, str) or not re.fullmatch('[a-zA-Z0-9._+-]{1,128}', leaf) or leaf in ('.', '..'):
                raise InstallError('installer_boot_path')
            if (root / 'boot').is_symlink():
                raise InstallError('installer_boot_path')
            path = root / 'boot' / leaf
            if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != receipt[kind + '_sha256']:
                raise InstallError('installer_boot_integrity')

    def _mount(self, device, path, mounts, filesystem):
        self.system.run(['/usr/bin/mount', device, str(path)])
        mounts.append(path)
        self.system.verify_mount(device, path, filesystem)

    def _runtime_mounts(self, root, plan, root_device, boot_device, mounts, operation_id):
        def prepare():
            for folder in ('dev', 'proc', 'sys'):
                path = root / folder
                path.mkdir(exist_ok=True)
                if path.is_symlink():
                    raise InstallError('installer_runtime_mount_symlink')
            self.system.run(['/usr/bin/mount', '-t', 'tmpfs', '-o', 'mode=0755,nosuid', 'tmpfs', str(root / 'dev')])
            mounts.append(root / 'dev')
            for device in (plan['target']['path'], root_device, boot_device, '/dev/null', '/dev/zero', '/dev/urandom'):
                target = root / 'dev' / Path(device).name
                target.touch()
                self.system.run(['/usr/bin/mount', '--bind', device, str(target)])
                mounts.append(target)
            self.system.run(['/usr/bin/mount', '-t', 'proc', '-o', 'nosuid,nodev,noexec', 'proc', str(root / 'proc')])
            mounts.append(root / 'proc')
            self.system.run(['/usr/bin/mount', '--bind', '/sys', str(root / 'sys')])
            mounts.append(root / 'sys')
            self.system.run(['/usr/bin/mount', '-o', 'remount,bind,ro', str(root / 'sys')])
        self._step(operation_id, 'private-runtime-mounts', prepare)

    def _grub(self, root, plan, boot, root_uuid):
        import hashlib
        if not isinstance(root_uuid, str) or not re.fullmatch('[A-Fa-f0-9-]{4,40}', root_uuid):
            raise InstallError('installer_filesystem_uuid')
        link = root / 'boot/grub/grub.cfg'
        expected_link = '../../etc/toddy/grub.cfg'
        for relative in ('boot', 'boot/grub', 'etc', 'etc/toddy'):
            path = root / relative
            if path.is_symlink():
                raise InstallError('installer_grub_parent_symlink')
            path.mkdir(mode=0o755, exist_ok=True)
        if link.is_symlink():
            if os.readlink(link) != expected_link:
                raise InstallError('installer_grub_link_not_canonical')
        elif link.exists():
            raise InstallError('installer_grub_layout_not_canonical')
        canonical_config = root / 'etc/toddy/grub.cfg'
        reference_sha = None
        if canonical_config.is_symlink() or (canonical_config.exists() and not canonical_config.is_file()):
            raise InstallError('installer_grub_conffile_not_regular')
        if canonical_config.exists():
            original = canonical_config.read_bytes()
            reference = root / 'usr/share/toddy/recovery/foundation-grub.cfg'
            if reference.exists() or reference.is_symlink():
                raise InstallError('installer_grub_recovery_reference_exists')
            regular(root, 'usr/share/toddy/recovery/foundation-grub.cfg', original, mode=0o444)
            reference_sha = hashlib.sha256(original).hexdigest()
        text = 'set timeout=5\nset default=0\n'
        for title, extra in [('Toddy OS', ''), ('Toddy text recovery', ' systemd.unit=multi-user.target')]:
            text += "menuentry '" + title + "' {\n search --no-floppy --fs-uuid --set=root " + root_uuid + '\n'
            text += ' linux /boot/' + boot['kernel'] + ' root=UUID=' + root_uuid + ' ro' + extra + '\n'
            text += ' initrd /boot/' + boot['initramfs'] + '\n}\n'
        # Preserve native package ownership/conffile identity: H09/H10 own the
        # real config in /etc and expose only this exact relative /boot link.
        regular(root, 'etc/toddy/grub.cfg', text.encode())
        if not link.is_symlink():
            os.symlink(expected_link, link)
        self.system.run(['/usr/sbin/chroot', str(root), '/usr/bin/grub-script-check', '/etc/toddy/grub.cfg'])
        prefix = ['/usr/sbin/chroot', str(root), '/usr/sbin/grub-install']
        if plan['options']['boot_mode'] == 'uefi':
            command = [*prefix, '--target=x86_64-efi', '--efi-directory=/boot/efi', '--bootloader-id=Toddy', '--no-nvram', '--removable']
        else:
            command = [*prefix, '--target=i386-pc', '--recheck', plan['target']['path']]
        self.system.run(command, timeout=120)
        if not link.is_symlink() or os.readlink(link) != expected_link or canonical_config.read_bytes() != text.encode():
            raise InstallError('installer_grub_postcondition')
        if reference_sha is not None and hashlib.sha256(reference.read_bytes()).hexdigest() != reference_sha:
            raise InstallError('installer_grub_recovery_reference_changed')
        return {'verified': True, 'config_path': '/etc/toddy/grub.cfg',
            'config_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'boot_link': expected_link, 'foundation_reference_sha256': reference_sha,
            'recovery_scope': 'text-login-current-installed-kernel; original foundation config retained as reference, not active builder-disk boot entry'}

    def _state(self, operation_id, state, step):
        self.journal.db.execute('UPDATE operations SET state=?,step=? WHERE id=?', (state, step, operation_id))

    def _receipt(self, operation_id, step, value):
        self.journal.db.execute('INSERT OR REPLACE INTO receipts VALUES(?,?,?)', (operation_id, step, json.dumps(value, sort_keys=True, separators=(',', ':'))))

    def _step(self, operation_id, step, action):
        self._state(operation_id, 'running-step', step)
        result = action()
        self._state(operation_id, 'step-finished', step)
        return result

    def _canceled(self, operation_id, cancel):
        return (cancel is not None and cancel.is_set()) or bool(self.journal.snapshot(operation_id)['cancel'])

    def _boundary(self, operation_id, cancel):
        if self._canceled(operation_id, cancel):
            raise InstallError('installer_canceled_at_safe_boundary_rescue_required')

    def _unmount(self, mounts):
        while mounts:
            path = mounts[-1]
            # No lazy/forced unmount: a busy writer needs reconciliation.
            self.system.run(['/usr/bin/umount', str(path)], timeout=30)
            mounts.pop()
