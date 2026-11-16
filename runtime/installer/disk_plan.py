"""Reviewed GPT/ext4 installation plan; pure validation never writes a device."""
import copy
import hashlib
import json
from pathlib import PurePosixPath
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MIB = 1024**2
GIB = 1024**3
GUIDS = {'root': '0FC63DAF-8483-4772-8E79-3D69D8477DE4',
         'esp': 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B',
         'bios': '21686148-6449-6E6F-744E-656564454649'}
DISK_FIELDS = {'path', 'major_minor', 'serial', 'size', 'sector_size', 'model', 'driver',
               'readonly', 'mounted', 'blank', 'virtual'}
OPTION_FIELDS = {'operation_id', 'boot_mode', 'username', 'uid', 'gid', 'locale',
                 'timezone', 'hostname', 'ai_choice', 'extras'}


class InstallError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def hash_value(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise InstallError('installer_hash')
    return value


def validate_disk(disk, *, require_blank=True):
    if not isinstance(disk, dict) or set(disk) != DISK_FIELDS:
        raise InstallError('installer_disk_schema')
    if not isinstance(disk['path'], str) or not re.fullmatch(r'/dev/[a-zA-Z0-9_-]+', disk['path']):
        raise InstallError('installer_disk_path')
    if not isinstance(disk['major_minor'], str) or not re.fullmatch('[0-9]+:[0-9]+', disk['major_minor']):
        raise InstallError('installer_disk_identity')
    if not isinstance(disk['serial'], str) or not 1 <= len(disk['serial']) <= 128 or any(ord(c) < 32 for c in disk['serial']):
        raise InstallError('installer_disk_serial')
    if type(disk['size']) is not int or not 8 * GIB <= disk['size'] <= 2**53 - 1 or disk['sector_size'] not in (512, 4096):
        raise InstallError('installer_disk_size')
    for key in ('readonly', 'mounted', 'blank', 'virtual'):
        if type(disk[key]) is not bool:
            raise InstallError('installer_disk_state')
    for key in ('model', 'driver'):
        if not isinstance(disk[key], str) or len(disk[key]) > 128:
            raise InstallError('installer_disk_identity')
    if disk['readonly'] or disk['mounted'] or (require_blank and not disk['blank']):
        raise InstallError('installer_target_not_blank_unmounted_writable')
    return disk


def make_plan(disk, options, payload):
    validate_disk(disk)
    if not isinstance(options, dict) or set(options) != OPTION_FIELDS:
        raise InstallError('installer_options_schema')
    if not isinstance(options['operation_id'], str) or not re.fullmatch('[0-9a-f]{32}', options['operation_id']):
        raise InstallError('installer_operation_id')
    if options['boot_mode'] not in ('uefi', 'bios'):
        raise InstallError('installer_firmware')
    if not isinstance(options['username'], str) or not re.fullmatch('[a-z][a-z0-9_-]{0,31}', options['username']) or options['username'] in ('root', 'lfs', 'tester', 'toddy', 'toddy-live', 'builder'):
        raise InstallError('installer_owner')
    if type(options['uid']) is not int or type(options['gid']) is not int or not 1000 <= options['uid'] <= 60000 or not 1000 <= options['gid'] <= 60000:
        raise InstallError('installer_owner_id')
    if options['locale'] not in ('en_US.UTF-8', 'pt_BR.UTF-8'):
        raise InstallError('installer_locale')
    timezone = options['timezone']
    if not isinstance(timezone, str) or len(timezone) > 128 or PurePosixPath(timezone).is_absolute() or '..' in timezone.split('/'):
        raise InstallError('installer_timezone')
    try:
        ZoneInfo(timezone)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise InstallError('installer_timezone') from exc
    if not isinstance(options['hostname'], str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,62}', options['hostname']) or options['hostname'].endswith('-'):
        raise InstallError('installer_hostname')
    if options['ai_choice'] not in ('later', 'api', 'local'):
        raise InstallError('installer_ai_choice')
    extras = options['extras']
    if not isinstance(extras, list) or any(not isinstance(item, str) or item not in ('docker', 'opencode', 'vscode') for item in extras) or len(extras) != len(set(extras)):
        raise InstallError('installer_optional_choice')
    if not isinstance(payload, dict) or set(payload) != {'sha256', 'catalog_sha256', 'bytes'} or type(payload['bytes']) is not int or not 0 < payload['bytes'] <= 2**53 - 1:
        raise InstallError('installer_payload_schema')
    hash_value(payload['sha256'])
    hash_value(payload['catalog_sha256'])
    sector = disk['sector_size']
    alignment = MIB // sector
    boot_size = 512 * MIB if options['boot_mode'] == 'uefi' else MIB
    boot_start = alignment
    boot_sectors = boot_size // sector
    root_start = boot_start + boot_sectors
    # Leave aligned headroom for backup GPT structures, never assume storage is
    # pre-zeroed. ext4 metadata/rescue headroom uses actual selected payload size.
    root_end = ((disk['size'] // sector - alignment) // alignment) * alignment
    root_sectors = root_end - root_start
    required = payload['bytes'] + max(2 * GIB, payload['bytes'] // 4) + 256 * MIB
    if root_sectors * sector < max(8 * GIB, required):
        raise InstallError('installer_insufficient_target_space')
    boot_kind = 'esp' if options['boot_mode'] == 'uefi' else 'bios'
    value = {'schema_version': 1, 'target': copy.deepcopy(disk), 'options': copy.deepcopy(options),
             'payload': copy.deepcopy(payload), 'partitions': [
                 {'number': 1, 'kind': boot_kind, 'start': boot_start, 'sectors': boot_sectors, 'type': GUIDS[boot_kind]},
                 {'number': 2, 'kind': 'root', 'start': root_start, 'sectors': root_sectors, 'type': GUIDS['root']}],
             'required_root_bytes': required, 'unsupported': ['dual-boot', 'encryption', 'secure-boot']}
    value['options']['extras'] = sorted(extras)
    return dict(value, plan_sha256=digest(value))


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {'schema_version', 'target', 'options', 'payload', 'partitions', 'required_root_bytes', 'unsupported', 'plan_sha256'}:
        raise InstallError('installer_plan_schema')
    if type(plan['schema_version']) is not int or plan['schema_version'] != 1 or digest({key: value for key, value in plan.items() if key != 'plan_sha256'}) != plan['plan_sha256']:
        raise InstallError('installer_plan_changed')
    expected = make_plan(plan['target'], plan['options'], plan['payload'])
    if expected != plan:
        raise InstallError('installer_plan_changed')
    return copy.deepcopy(expected)


def partition_script(plan):
    plan = validate_plan(plan)
    lines = ['label: gpt', 'unit: sectors', 'sector-size: ' + str(plan['target']['sector_size']), '']
    for partition in plan['partitions']:
        lines.append('start={start}, size={sectors}, type={type}'.format(**partition))
    return '\n'.join(lines) + '\n'


class QualificationPolicy:
    """Development qualification only; never treat a serial as owner consent."""
    def __init__(self, serial):
        if not isinstance(serial, str) or not serial.startswith('TODDY-INSTALL-'):
            raise InstallError('installer_qualification_serial')
        self.serial = serial

    def check(self, disk):
        if not disk['virtual'] or disk['serial'] != self.serial:
            raise InstallError('installer_qualification_target')


class ProductionPolicy:
    """Owner-selected production path, separately confirmed exact physical disk.

    This source support is not evidence that physical hardware was tested.
    """
    def check(self, disk):
        validate_disk(disk)
