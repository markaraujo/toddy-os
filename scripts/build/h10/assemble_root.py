#!/usr/bin/env python3
"""Assemble a fresh uncompressed foundation root under milestone/build locks.

Keep every stage/report on failure and start a new generation after diagnosis.
An assembled root is not compression, initramfs, boot or release acceptance.
"""
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
for directory in (HERE.parent, HERE.parent / 'h08', HERE.parent / 'h11', HERE):
    sys.path.insert(0, str(directory))
import acl_sidecar
import copy_selected_root
import fresh_directories
import image_attribution
import image_payload
import info_index
import live_accounts
import live_configuration
import live_console
import loader_cache
import offline_services
import package_database
import root_inventory
import remove_image_qa
import review_image_key_markers
from package_backend import PackageBackend
from python_qa_transaction import atomic_json

BUILD = Path('/var/log/toddy/build')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_destinations(root, image, work):
    if image.is_relative_to(work) or work.is_relative_to(image):
        raise ValueError('Image and evidence must be disjoint fresh generations')
    for path in (image, work):
        if (path.resolve() != path or path.exists() or path.is_symlink()
                or not any(path != root / area and path.is_relative_to(root / area)
                           for area in ('tmp', 'sources/stage'))):
            raise ValueError('Preserve existing/outside/redirected assembly generation')
        info = path.parent.stat()
        if (path.parent.resolve() != path.parent or not stat.S_ISDIR(info.st_mode)
                or info.st_uid != 0 or info.st_gid != 0 or info.st_mode & 0o022
                or info.st_dev != root.stat().st_dev):
            raise ValueError('Assembly parent must be a private root-owned target directory')


def assemble(backend, image, work, *, release=False, repository=PROJECT,
             records=Path('/var/log/toddy/packages'), cache=Path('/var/cache/toddy/packages')):
    """Component entry point; the production CLI below owns the exclusive gate."""
    image, work, root = Path(image), Path(work), backend.target
    if not backend.native or os.geteuid() != 0 or root.resolve() != root:
        raise ValueError('Assembly requires the accepted native disposable target')
    validate_destinations(root, image, work)
    baseline_path = repository / 'config/live-account-baseline.json'
    baseline = json.loads(baseline_path.read_text())
    live_accounts.account_data(baseline)
    work.mkdir(mode=0o700)
    journal = {'started': now(), 'image': str(image), 'evidence': str(work),
               'release_profile': release, 'assembler_sha256': digest(Path(__file__)),
               'baseline_sha256': digest(baseline_path), 'actions': [], 'assembled': False,
               'release_accepted': False, 'boot_verified': False}
    journal_path = work / 'assembly.json'
    atomic_json(journal_path, journal)

    def step(name, action):
        entry = {'step': name, 'started': now(), 'finished': None}
        journal['actions'].append(entry)
        atomic_json(journal_path, journal)
        print('ASSEMBLY_STAGE ' + name, flush=True)
        result = action()
        path = work / f'{len(journal["actions"]):02d}-{name}.json'
        atomic_json(path, result)
        entry.update(finished=now(), report=path.name, sha256=digest(path))
        atomic_json(journal_path, journal)
        return result

    previous_umask = os.umask(0o022)
    try:
        # Use exactly the same module/descriptor registry as stage_database.
        # Nested copying must not release the outer POSIX source read locks.
        with package_database.database_lock(root / 'var/lib/dpkg'):
            source_database = package_database.snapshot(root / 'var/lib/dpkg')
            inventory = step('source-inventory', lambda: root_inventory.inspect_installed(backend, records, cache))
            required = {'toddy-base-config', 'toddy-boot-config', 'linux-kernel', 'squashfs-tools', 'apt', 'dpkg'}
            if not required <= inventory['packages'].keys():
                raise ValueError('Required accepted foundation packages are absent')
            if inventory['owners'].get('/etc/fstab') != ['toddy-base-config']:
                raise ValueError('Source fstab lacks the accepted base configuration owner')
            if release and not {'python', 'python-test-support'} <= inventory['packages'].keys():
                raise ValueError('Complete the gated native Python QA ownership transfer before release assembly')
            total = sum((root / name).lstat().st_size for name in inventory['names']
                        if 'sha256' in inventory['entries'].get('/' + name, {}))
            reserve = 2 * total + 2048 * len(inventory['names']) + 2 * 1024 ** 3
            space = os.statvfs(work)
            if space.f_bavail * space.f_frsize < reserve:
                raise ValueError('Insufficient space for fresh payload, retained Tar evidence and reserve')
            copied_report = step('copy-payload', lambda: copy_selected_root.copy_selected(
                backend, root, image, work / 'copy', inventory['names'], records))
            copied_path = work / 'copy' / copied_report['input_manifest']
            if digest(copied_path) != copied_report['input_manifest_sha256']:
                raise ValueError('Preserved copy-input manifest differs')
            copied = json.loads(copied_path.read_text())
            fresh = step('fresh-directories', lambda: fresh_directories.stage_directories(
                backend, image, inventory['fresh_directories'], baseline))
            step('native-database', lambda: package_database.stage_database(backend, image / 'var/lib/dpkg', records))

            def package_record(name):
                version, architecture, state = backend.run('dpkg-query', '-W',
                    '-f=${Version}\t${Architecture}\t${Status}', name,
                    capture_output=True, text=True).stdout.split('\t')
                path = records / f'{name}_{version}_{architecture}.json'
                if (state != 'install ok installed' or version != inventory['packages'][name]['version']
                        or digest(path) != inventory['verification']['record_sha256'][str(path)]):
                    raise ValueError('Source package generation changed during assembly')
                return json.loads(path.read_text())

            if release:
                step('remove-optional-qa', lambda: remove_image_qa.remove_image_qa(backend, image,
                    package_record('python'), package_record('python-test-support'), work / 'qa-removal.json'))
            database_state = step('image-database-state', lambda: package_database.snapshot(image / 'var/lib/dpkg'))
            step('fresh-accounts', lambda: live_accounts.stage_accounts(image, baseline))
            step('live-configuration', lambda: live_configuration.stage_live_configuration(
                backend, image, inventory['entries']['/etc/fstab']['sha256'],
                live_configuration.DEFAULT_LINKS, records))
            step('offline-services', lambda: offline_services.configure_services(backend, image, records))
            step('live-console', lambda: live_console.stage_console(image))
            cache_report = step('loader-cache', lambda: loader_cache.generate_loader_cache(backend, image, inventory['entries']))
            info_report = step('info-index', lambda: info_index.generate_info_index(backend, image, inventory['entries']))
            acl_report = step('acl-sidecar', lambda: acl_sidecar.stage_acl(backend, image, records))
            payload = step('owned-payload-audit', lambda: image_payload.audit(
                backend, image, records, cache, live_profile=True))
            expected_packages = set(inventory['packages']) - ({'python-test-support'} if release else set())
            if not payload['owned_payload_check_passed'] or set(payload['package_names']) != expected_packages:
                raise ValueError('Final native image payload or package set differs; preserve audit findings')
            owned = {}
            for name, sha in payload['record_sha256'].items():
                path = Path(name)
                if digest(path) != sha:
                    raise ValueError('Native provenance changed before image attribution')
                record = json.loads(path.read_text())
                owned[record['name']] = record
            plan = image_attribution.owned_plan(owned, copied)
            image_attribution.declare_fresh(plan, fresh)
            image_attribution.declare_database(plan, database_state)
            image_attribution.declare_accounts(plan, baseline)
            image_attribution.declare_live_profile(plan)
            for kind, report in (('loader-cache', cache_report), ('info-index', info_report), ('acl-sidecar', acl_report)):
                image_attribution.declare_artifact(plan, kind, report)
            step('image-attribution-plan', lambda: plan)
            attributed = step('image-attribution-audit', lambda: image_attribution.audit(
                backend, image, plan, copied['hardlink_groups']))
            if not attributed['attribution_check_passed']:
                raise ValueError('Image contains missing, changed or undeclared state; preserve attribution report')
            if release:
                markers = step('key-marker-review', lambda: review_image_key_markers.review(
                    backend, image, repository, records, cache))
                if not markers['private_key_marker_check_passed']:
                    raise ValueError('Image key-marker review has unresolved findings')
            manifest = step('image-manifest', lambda: copy_selected_root.snapshot(
                image, copy_selected_root.tree_names(image)))
            if (package_database.snapshot(root / 'var/lib/dpkg') != source_database
                    or any(digest(Path(path)) != sha for path, sha in inventory['verification']['record_sha256'].items())
                    or digest(baseline_path) != journal['baseline_sha256']):
                raise ValueError('Source package/account generation changed during assembly')
            journal.update(assembled=True, finished=now(), configured_packages=payload['configured_packages'],
                image_entries=len(manifest['entries']),
                pending_acceptance=['dependency closure audit',
                    'complete credential/identity/license inspection', 'compression and initramfs assembly',
                    'actual BIOS/UEFI/virtual USB boot and live behavior'])
            atomic_json(journal_path, journal)
            return journal
    except BaseException as error:
        journal.update(failed_at=now(), failure_type=type(error).__name__, failure=str(error), assembled=False)
        if isinstance(error, subprocess.CalledProcessError):
            journal['native_failure'] = {'exit': error.returncode,
                **{key: value.decode(errors='replace') if isinstance(value, bytes) else value
                   for key in ('stdout', 'stderr') if (value := getattr(error, key)) is not None}}
        atomic_json(journal_path, journal)
        raise
    finally:
        os.umask(previous_umask)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--release', action='store_true', help='Require H11 and remove optional QA before final auditing')
    args = parser.parse_args()
    gate = HERE.parent / 'h11/require_gate.py' if args.release else HERE / 'require_gate.py'
    subprocess.run(['python3', str(gate)], check=True)
    if not all(path.is_relative_to(Path('/mnt/lfs/sources/stage')) for path in (args.image, args.evidence)):
        raise ValueError('Production generations must use designated target staging storage')
    # This CLI is its own assembly operation, not a child of run_step.py. Never
    # nest it under a dispatcher holding this same exclusive flock.
    with (BUILD / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (BUILD / 'input-sync.running').exists() or list(BUILD.glob('*.running.json')):
            raise ValueError('Preserve unfinished build/sync state before image assembly')
        marker = json.loads((BUILD / 'h10-squashfs-tools.success.json').read_text())
        if marker.get('recipe_exit') != 0 or marker.get('postcheck_exit') != 0:
            raise ValueError('Native Squashfs tooling has not passed its postcheck')
        print(json.dumps(assemble(PackageBackend(), args.image, args.evidence, release=args.release), indent=2))


if __name__ == '__main__':
    main()
