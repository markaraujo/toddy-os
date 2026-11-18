"""Export current archive-backed offline/live closures in the designated builder.

Read-only with respect to the native target and package database. The only output
is a new private generation. This is input custody, never image/boot acceptance.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import offline_payload as payload

ROOT = Path('/opt/toddy-build')
TARGET = Path('/mnt/lfs')
OUTPUT = TARGET / 'sources/stage/toddy-image-projection-2'
RECORDS = Path('/var/log/toddy/packages')
ARCHIVES = Path('/var/cache/toddy/packages')
BUILD = Path('/var/log/toddy/build')
ADDITIONS = frozenset(payload.MANDATORY_ADDITIONS)
LIVE = frozenset(('calamares', 'toddy-installer', 'calamares-branding-toddy'))
FORBIDDEN = frozenset(payload.ACQUIRED) | {'rustc'}


def installed_rows(text):
    rows = {}
    for line in text.splitlines():
        fields = line.split('\t')
        if len(fields) != 6:
            raise ValueError('Native inventory field count')
        name, version, architecture, state, depends, pre_depends = fields
        if not payload.NAME.fullmatch(name) or not payload.VERSION.fullmatch(version) or name in rows:
            raise ValueError('Native inventory identity')
        if state != 'install ok installed' or architecture not in ('amd64', 'all'):
            raise ValueError('Native inventory must be fully configured')
        rows[name] = dict(name=name, version=version, architecture=architecture,
                          depends=depends, pre_depends=pre_depends)
    if not rows:
        raise ValueError('Empty native inventory')
    return rows


def select(profile, rows):
    roots = set(profile['retained_foundation_packages']) | set(profile['desktop_roots'])
    base = payload.dependency_closure(rows, roots | ADDITIONS)
    live = payload.dependency_closure(rows, roots | ADDITIONS | LIVE)
    _delivery_class, allowed_acquired = payload.delivery_policy(profile)
    forbidden = FORBIDDEN - allowed_acquired
    if base & (forbidden | LIVE | {'qtbase'}) or live & forbidden:
        raise ValueError('Acquired/build-only root leaked into image closure')
    if (base - ADDITIONS) & set(profile['excluded_product_roots']):
        raise ValueError('Offline projection contradicts frozen exclusions')
    return base, live


def original_source_provenance(component, record, *, repository=ROOT, target=TARGET):
    """Admit reviewed original code without inventing an upstream archive."""
    if record.get('source_kind') != 'book-derived-versioned-recipe':
        raise ValueError('Foreign package lacks upstream source custody')
    for relative in ('docs/evidence/B02-desktop-runtime-manifest.json', 'docs/evidence/H11-components.json'):
        evidence = payload.strict((repository/relative).read_bytes())
        for row in evidence['components']:
            if (row['name'] == component['name'] and not row.get('sources') and
                    row.get('component_record_sha256') == component['component_record_sha256']):
                return 'committed-original-record'
    if component['name'] not in {'toddy-assistant', 'toddy-branding', 'toddy-installer', 'calamares-branding-toddy', 'toddy-agent', 'toddy-executor', 'toddy-desktop-defaults', 'toddy-voice', 'toddy-integrations', 'toddy-voice-native-catalog'}:
        raise ValueError('Unreviewed original package identity')
    supporting = record.get('supporting_build_scripts', {})
    files = supporting.get('files')
    if not isinstance(files, dict) or not files or any(not isinstance(k, str) or
            not payload.HASH.fullmatch(v) for k,v in files.items()):
        raise ValueError('Original recipe closure missing')
    canonical = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    if hashlib.sha256(canonical).hexdigest() != supporting.get('sha256') or component['recipe_sha256'] not in files.values() or record.get('packager_sha256') not in files.values():
        raise ValueError('Original recipe closure integrity')
    if component['name'] == 'toddy-voice-native-catalog':
        from voice_catalog_provenance import verify_catalog_provenance
        return verify_catalog_provenance(component, record, repository=repository, target=target)
    virtual = '/usr/share/doc/' + component['name'] + '/source-manifest.json'
    expected = record['payload'].get(virtual, {}).get('sha256')
    manifest_path = payload.regular(target/virtual.lstrip('/'))
    if not expected or payload.digest(manifest_path) != expected:
        raise ValueError('Original source manifest ownership differs')
    manifest = payload.strict(manifest_path.read_bytes())
    inputs = manifest.get('source_inputs', manifest.get('inputs'))
    if manifest.get('package') != component['name'] or not isinstance(inputs, dict) or not inputs:
        raise ValueError('Original source manifest identity')
    for relative, value in inputs.items():
        payload.canonical(relative, absolute=False)
        if isinstance(value, dict):
            if set(value) != {'sha256', 'bytes'} or type(value['bytes']) is not int or value['bytes'] < 0:
                raise ValueError('Original source manifest size')
            value = value['sha256']
        if not isinstance(value, str) or not payload.HASH.fullmatch(value):
            raise ValueError('Original source manifest integrity')
    return 'owned-original-source-manifest'


def collect(names, rows, records=RECORDS, archives=ARCHIVES, *, storage=None):
    components = {}
    for name in sorted(names):
        row = rows[name]
        record = records / (name + '_' + row['version'] + '_' + row['architecture'] + '.json')
        measured={}
        component = payload.component_from_record(record, archives, storage=measured)
        if storage is not None:storage[name]=measured
        if (component['depends'] != row['depends'] or row['pre_depends']):
            raise ValueError('Observed dependencies differ or Pre-Depends is unqualified: ' + name)
        # component_from_record validates archive/control/owned bytes/legal data;
        # also pin source/recipe integrity now, before asking for a signing input.
        if not payload.HASH.fullmatch(component['recipe_sha256']):
            raise ValueError('Missing source/recipe custody: ' + name)
        if not component['sources']:
            original_source_provenance(component, payload.strict(payload.regular(record).read_bytes()))
        for source in component['sources']:
            if not payload.HASH.fullmatch(source.get('sha256', '')):
                raise ValueError('Missing source integrity: ' + name)
        components[name] = component
    return components


def documents(profile_bytes, inventory, components):
    profile = payload.strict(profile_bytes)
    rows = installed_rows(inventory)
    base, live = select(profile, rows)
    if set(components) != live:
        raise ValueError('Archive-backed set differs from selected live union')
    projection = {'schema_version': 1,
        'scope': 'B12 current native offline archive closure; not an installed image',
        'profile_sha256': hashlib.sha256(profile_bytes).hexdigest(),
        'observed_inventory_sha256': hashlib.sha256(inventory.encode()).hexdigest(),
        'components': [components[n] for n in sorted(base - ADDITIONS)]}
    delivery_class, allowed_acquired = payload.delivery_policy(profile)
    live_profile = dict(profile, scope='B12 live-only current native archive closure',
        desktop_roots=sorted(set(profile['desktop_roots']) | ADDITIONS | LIVE),
        excluded_product_roots=sorted(FORBIDDEN - allowed_acquired))
    if delivery_class is not None:
        projection.update(delivery_class=delivery_class, g2_eligible=False, automatic_activation=False, scope='MVP preinstalled backend archive closure; no G2 acceptance')
        live_profile.update(scope='MVP preinstalled live archive closure; no G2 acceptance')
    live_bytes = payload.encoded(live_profile)
    live_projection = dict(projection,
        scope=('MVP live archive closure; included backend stays owner opt-in; no G2 acceptance' if delivery_class is not None else 'B12 live image archive closure; excludes acquired agent/model packages'),
        profile_sha256=hashlib.sha256(live_bytes).hexdigest(),
        components=[components[n] for n in sorted(live)])
    return {'profile.json': profile_bytes, 'projection.json': payload.encoded(projection),
        'additional-components.json': payload.encoded([components[n] for n in sorted(ADDITIONS)]),
        'live-profile.json': live_bytes, 'live-projection.json': payload.encoded(live_projection),
        'split.json': payload.encoded({'version': 1, 'offline': sorted(base),
            'live_only': sorted(live-base), 'unselected': sorted(set(rows)-live),
            'projection_only_no_target_file_copy': True,
            'configured_image': False, 'boot_verified': False})}


def save_generation(output, files):
    # No overwrite/resume mode. A partial generation is retained for inspection.
    output.mkdir(mode=0o700)
    hashes = {}
    for name, data in sorted(files.items()):
        if not re.fullmatch(r'[a-z][a-z-]*\.json', name):
            raise ValueError('Nonliteral projection output')
        with (output/name).open('xb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        hashes[name] = hashlib.sha256(data).hexdigest()
    with (output/'complete.json').open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(payload.encoded({'version': 1, 'files': hashes,
            'producer_sha256': payload.digest(Path(__file__)), 'native_target_changed': False}))
        stream.flush(); os.fsync(stream.fileno())
    directory = os.open(output, os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def main():
    if sys.argv[1:] not in ([], ['--mvp']) or os.getuid() != 0 or os.geteuid() != 0 or Path(__file__).resolve() != ROOT/'scripts/build/phase2/image_projection.py':
        raise ValueError('Fixed coordinator-only designated-builder command')
    mvp = sys.argv[1:] == ['--mvp']
    output = TARGET / 'sources/stage/toddy-mvp-image-projection-6' if mvp else OUTPUT
    profile_name = 'config/phase2/mvp-desktop-runtime-roots.json' if mvp else 'config/phase2/desktop-runtime-roots.json'
    os.umask(0o077)
    subprocess.run(['/usr/bin/bash', '-c',
        'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    with (BUILD/'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(BUILD.glob('*.running.json')) or (BUILD/'input-sync.running').exists():
            raise ValueError('Preserve running native operation')
        parent = output.parent
        info = parent.lstat()
        if parent.resolve() != parent or info.st_uid or info.st_gid or info.st_mode & 0o022 or info.st_dev != TARGET.stat().st_dev:
            raise ValueError('Projection output requires protected same-filesystem stage')
        if os.path.lexists(output):
            raise ValueError('Preserve previous projection generation')
        command = ['/usr/sbin/chroot', str(TARGET), '/usr/bin/dpkg-query', '-W',
            '-f=${binary:Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\t${Pre-Depends}\n']
        inventory = subprocess.check_output(command, text=True, timeout=60)
        profile_bytes = (ROOT/profile_name).read_bytes()
        rows = installed_rows(inventory)
        _, names = select(payload.strict(profile_bytes), rows)
        measurements={}
        components = collect(names, rows, storage=measurements)
        if subprocess.check_output(command, text=True, timeout=60) != inventory:
            raise ValueError('Native inventory changed during projection')
        files=documents(profile_bytes, inventory, components)
        base,live=select(payload.strict(profile_bytes),rows)
        reports={}
        for kind,selected in (('offline',base),('live',live)):
            records=[payload.strict(payload.regular(RECORDS/(name+'_'+rows[name]['version']+'_'+rows[name]['architecture']+'.json')).read_bytes()) for name in sorted(selected)]
            reports[kind]=payload.storage_measurements({name:measurements[name] for name in selected},payload.inventory(records),os.statvfs(output.parent).f_frsize)
        files['storage-report.json']=payload.encoded({'version':1,'scope':'actual-archive-measurements-not-signed-preparation-or-native-acceptance',
            'profiles':reports,'required_reserve_bytes':payload.RESERVE_BYTES,'generated_policy_and_embedded_inputs_still_required':True})
        save_generation(output,files)
    print(json.dumps({'state': 'archive-backed-projection', 'output': str(output),
        'production_ready': False, 'boot_verified': False}, sort_keys=True))


if __name__ == '__main__':
    main()
