"""Frozen Calamares3.4.3 project adapter around the actual installer backend.

Only installed trusted bindings can supply package/image/account/boot callbacks.
No candidate JSON selects scripts, payload paths, policy, state paths or tools.
"""
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import select
import stat
import threading
import time

from ..backend import Installer
from ..disk_plan import InstallError, make_plan, validate_plan, hash_value
from ..linux_disk import LinuxDisk

MAX_JSON = 32768
REQUIRED_READY = {'verified', 'payload_manifest_sha256', 'catalog_sha256',
                  'finalizer_source_sha256', 'native_qualification_report_sha256', 'supported_firmware'}
PHASES = ['preflight', 'partition-table', 'partition-postcondition', 'root-filesystem',
          'esp-filesystem', 'mount-target', 'composed-payload', 'mount-esp',
          'installed-identity', 'private-runtime-mounts', 'fresh-owner-login',
          'installed-initramfs', 'grub', 'installed-hygiene', 'deferred-setup-handoff',
          'sync-installed-state', 'complete']


def strict(data):
    if type(data) is not bytes or not 0 < len(data) <= MAX_JSON:
        raise InstallError('installer_calamares_json_bound')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise InstallError('installer_calamares_duplicate_json')
            result[key] = value
        return result
    def reject(_):
        raise InstallError('installer_calamares_json_number')
    try:
        result = json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                            parse_float=reject, parse_constant=reject)
        # Plan values interchange exactly between Qt JSON/Python. No surrogate
        # or integer too large for its numeric representation can sneak through.
        def check(value, depth=0):
            if depth > 32:
                raise ValueError('depth')
            if isinstance(value, str):
                value.encode('utf-8', errors='strict')
            elif isinstance(value, dict):
                for key, item in value.items():
                    check(key, depth + 1); check(item, depth + 1)
            elif isinstance(value, list):
                for item in value:
                    check(item, depth + 1)
            elif type(value) is int and abs(value) > 2**53 - 1:
                raise ValueError('number')
        check(result)
        return result
    except InstallError:
        raise
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise InstallError('installer_calamares_json_invalid') from None


def encoded(value):
    body = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    strict(body)
    return body


def sealed_json(descriptor, *, uid=None):
    if type(descriptor) is not int or descriptor < 3:
        raise InstallError('installer_private_descriptor_required')
    uid = os.geteuid() if uid is None else uid
    info = os.fstat(descriptor)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 0 or not 0 < info.st_size <= MAX_JSON):
        raise InstallError('installer_sealed_descriptor_required')
    required = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
    if fcntl.fcntl(descriptor, fcntl.F_GET_SEALS) & required != required:
        raise InstallError('installer_sealed_descriptor_required')
    data = os.pread(descriptor, MAX_JSON + 1, 0)
    if len(data) != info.st_size:
        raise InstallError('installer_sealed_descriptor_changed')
    return strict(data)


def private_pipe(descriptor, *, uid=None):
    if type(descriptor) is not int or descriptor < 3:
        raise InstallError('installer_private_descriptor_required')
    info = os.fstat(descriptor)
    if (not stat.S_ISFIFO(info.st_mode) or info.st_uid != (os.geteuid() if uid is None else uid)
            or stat.S_IMODE(info.st_mode) & 0o077
            or fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_ACCMODE != os.O_RDONLY):
        raise InstallError('installer_private_pipe_required')
    return descriptor


def process_start_ticks(pid):
    raw = Path('/proc', str(pid), 'stat').read_bytes()
    return int(raw.rsplit(b') ', 1)[1].split()[19])


class SealedConfirmation:
    """Short-lived human UI decision, independent of the candidate plan.

    Default production creator is the actual root Calamares parent, authenticated
    by kernel process identity/boot/start time and immutable inherited descriptor.
    Test constructor overrides are source injection only, never CLI arguments.
    Root itself is not isolated from root; it already has unrestricted disk power.
    """
    def __init__(self, descriptor, *, creator_pid=None, executable='/usr/bin/calamares',
                 clock=time.monotonic, uid=None):
        self.body = sealed_json(descriptor, uid=uid)
        self.clock = clock
        self.creator_pid = os.getppid() if creator_pid is None else creator_pid
        self.executable = executable
        fields = {'version', 'plan_sha256', 'target_serial', 'creator_pid', 'creator_start_ticks',
                  'boot_id', 'issued_monotonic_ms', 'expires_monotonic_ms'}
        body = self.body
        if (not isinstance(body, dict) or set(body) != fields or type(body['version']) is not int or body['version'] != 1
                or type(body['creator_pid']) is not int or body['creator_pid'] != self.creator_pid
                or type(body['creator_start_ticks']) is not int or body['creator_start_ticks'] <= 0
                or type(body['issued_monotonic_ms']) is not int or type(body['expires_monotonic_ms']) is not int
                or not 0 < body['expires_monotonic_ms'] - body['issued_monotonic_ms'] <= 600000
                or not isinstance(body['target_serial'], str) or not body['target_serial']
                or not isinstance(body['boot_id'], str) or not re.fullmatch(r'[0-9a-f-]{36}', body['boot_id'])):
            raise InstallError('installer_human_confirmation_invalid')
        hash_value(body['plan_sha256'])

    def __call__(self, plan):
        try:
            body = self.body
            now = int(self.clock() * 1000)
            if (not body['issued_monotonic_ms'] <= now < body['expires_monotonic_ms']
                    or body['plan_sha256'] != plan['plan_sha256'] or body['target_serial'] != plan['target']['serial']
                    or Path('/proc/sys/kernel/random/boot_id').read_text().strip() != body['boot_id']
                    or process_start_ticks(self.creator_pid) != body['creator_start_ticks']):
                return False
            if self.executable is not None:
                if os.readlink('/proc/' + str(self.creator_pid) + '/exe') != self.executable:
                    return False
                identity = next(line for line in Path('/proc', str(self.creator_pid), 'status').read_text().splitlines() if line.startswith('Uid:'))
                if [int(value) for value in identity.split()[1:]] != [0, 0, 0, 0]:
                    return False
            return True
        except (OSError, ValueError, IndexError, StopIteration):
            return False


class PipeCancellation:
    """Control byte/EOF requests a safe boundary; never kills a native writer."""
    def __init__(self, descriptor):
        self.descriptor = private_pipe(descriptor)
        self.event = threading.Event()
    def is_set(self):
        if not self.event.is_set() and select.select([self.descriptor], [], [], 0)[0]:
            # Both an explicit byte and a vanished parent/EOF stop new dispatch.
            os.read(self.descriptor, 1)
            self.event.set()
        return self.event.is_set()
    def request(self):
        self.event.set()


class ReportingInstaller(Installer):
    def __init__(self, *arguments, observer=lambda _event: None, **keywords):
        super().__init__(*arguments, **keywords)
        self.observer = observer
    def _state(self, operation_id, state, step):
        super()._state(operation_id, state, step)
        if step in PHASES:
            self.observer({'version': 1, 'kind': 'progress', 'operation_id': operation_id,
                           'state': state, 'step': step,
                           'progress_milli': 1000 if state == 'completed' else int(PHASES.index(step) * 1000 / len(PHASES))})


class CalamaresAdapter:
    def __init__(self, bindings, *, system=None):
        self.bindings = bindings
        self.system = system if system is not None else LinuxDisk()

    def readiness(self):
        # The fixed installed factory is responsible for reading/checking actual
        # native report/artifact bytes. Candidate JSON cannot mint this object.
        report = self.bindings.readiness()
        if (not isinstance(report, dict) or set(report) != REQUIRED_READY or report['verified'] is not True
                or not isinstance(report['supported_firmware'], list) or not report['supported_firmware']
                or set(report['supported_firmware']) - {'bios', 'uefi'}
                or len(report['supported_firmware']) != len(set(report['supported_firmware']))):
            raise InstallError('installer_native_closure_not_qualified')
        for field in REQUIRED_READY - {'verified', 'supported_firmware'}:
            hash_value(report[field])
        # Callable presence is not readiness: the finalizer source/native report
        # bindings above are mandatory and checked by the actual fixed factory.
        for field in ('payload', 'policy', 'build_boot', 'save_pending', 'payload_identity'):
            if not hasattr(self.bindings, field):
                raise InstallError('installer_live_binding_incomplete')
        return copy.deepcopy(report)

    def review(self, device, options):
        ready = self.readiness()
        # The fixed production binding has the actual fresh account policy.
        # Check it even for no-write review; namespace collisions must not wait
        # until native groupadd/useradd after disk mutation.
        validate_options = getattr(self.bindings, 'validate_options', None)
        if validate_options is not None:
            validate_options(options)
        payload = self.bindings.payload_identity()
        if (payload.get('sha256') != ready['payload_manifest_sha256'] or
                payload.get('catalog_sha256') != ready['catalog_sha256']):
            raise InstallError('installer_live_payload_identity_changed')
        disk = self.system.probe(device)
        self.bindings.policy.check(disk)
        plan = make_plan(disk, options, payload)
        if options['boot_mode'] not in ready['supported_firmware']:
            raise InstallError('installer_firmware_not_qualified')
        # Actual Installer plan-only method cannot dispatch a native operation.
        result = self._installer(None).execute(plan)
        if result != {'state': 'review_required', 'plan': plan, 'disk_writes': False}:
            raise InstallError('installer_review_postcondition')
        return {'version': 1, 'state': 'review_required', 'plan_json': encoded(plan).decode(), 'disk_writes': False}

    def _installer(self, journal, observer=lambda _event: None):
        return ReportingInstaller(journal, policy=self.bindings.policy,
            verify_payload=self.bindings.payload.verify_payload,
            install_payload=self.bindings.payload.install_payload,
            build_boot=self.bindings.build_boot, save_pending=self.bindings.save_pending,
            system=self.system, observer=observer)

    def execute(self, plan, journal, *, confirmation, credential_fd, cancel,
                observer=lambda _event: None):
        plan = validate_plan(plan)
        ready = self.readiness()
        if (plan['payload']['sha256'] != ready['payload_manifest_sha256']
                or plan['payload']['catalog_sha256'] != ready['catalog_sha256']
                or plan['options']['boot_mode'] not in ready['supported_firmware']):
            raise InstallError('installer_live_payload_identity_changed')
        private_pipe(credential_fd)
        if confirmation(plan) is not True:
            raise InstallError('installer_current_destructive_authorization_required')
        # PreparedPayload's real signed-bundle verification runs again inside
        # Installer before first write and before/after actual target assembly.
        result = self._installer(journal, observer).execute(plan, confirmation=plan['plan_sha256'],
            authorize=confirmation, credential_fd=credential_fd, cancel=cancel)
        if result.get('state') not in {'completed', 'canceled-before-write'}:
            raise InstallError('installer_transaction_not_verified')
        return result
