#!/usr/bin/env python3
"""Private installer4 source delta: reuse reviewed328 materials, never authorize publication."""
import argparse
from contextlib import contextmanager
import hashlib
from pathlib import Path
import os
import shutil
import sys
import tarfile

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]
import package_sources as s
import package_sources_mvp as mvp
import package_sources_reviewed as accepted

p = s.p
KIND = 'native-package-source-review-delta-draft'
TARGET = 'toddy-installer'
OLD_VERSION = '0.2.0-1+toddy1'
NEW_VERSION = '0.2.0-1+toddy4'


def changes(base_packages, packages):
    old = {row['name']: row for row in base_packages}; new = {row['name']: row for row in packages}
    if set(old) != set(new) or len(old) != len(base_packages) or len(new) != len(packages):
        raise ValueError('Exact same native package names required for bounded delta')
    changed = [name for name in old if accepted.identity(old[name]) != accepted.identity(new[name])]
    if changed != [TARGET] or old[TARGET]['version'] != OLD_VERSION or new[TARGET]['version'] != NEW_VERSION:
        raise ValueError('Only actual installer1 to installer4 source transition allowed')
    return [name for name in old if name != TARGET]


def installer_inputs(repository, package, records):
    record_path = s.regular(records / (TARGET + '_' + NEW_VERSION + '_' + package['architecture'] + '.json'))
    if p.digest(record_path) != package['component_record_sha256']: raise ValueError('Actual current installer source record required')
    record = p.strict(record_path.read_bytes()); data = None
    virtual = '/usr/share/doc/toddy-installer/source-manifest.json'
    with p.tar_stream(repository / package['asset'], '--fsys-tarfile') as archive:
        for member in archive:
            if member.isfile() and '/' + member.name.removeprefix('./') == virtual:
                if member.size > 32 * 1024**2: raise ValueError('Bounded owned installer source manifest required')
                data = archive.extractfile(member).read()
    if data is None or hashlib.sha256(data).hexdigest() != record['payload'][virtual]['sha256']: raise ValueError('Owned installer source manifest missing or changed')
    manifest = p.strict(data)
    if manifest.get('package') != TARGET or manifest.get('version') != NEW_VERSION or not manifest.get('inputs'): raise ValueError('Actual installer4 preferred project input declaration required')
    return {(name, value['sha256'] if isinstance(value, dict) else value) for name, value in manifest['inputs'].items()}


class Prior:
    def __init__(self, directory, inventory, decision):
        self.directory = directory
        self.inventory = inventory
        self.rows = {row['path']: row for row in inventory['members']}
        self.index = {}; self.archives = []; self.asset_members = {}
        for asset in inventory['source_assets']:
            path = s.regular(directory / asset['name'])
            if p.digest(path) != asset['sha256'] or path.stat().st_size != asset['bytes']:
                raise ValueError('Actual reviewed backbone source tar changed')
            archive = tarfile.open(path, 'r:'); self.archives.append(archive)
            self.asset_members[asset['name']] = []
            for member in archive:
                if not member.isfile() or member.name not in self.rows or member.name in self.index or member.size != self.rows[member.name]['bytes']:
                    raise ValueError('Backbone member namespace/size changed')
                self.index[member.name] = (archive, member)
                self.asset_members[asset['name']].append(member.name)
        if set(self.index) != set(self.rows): raise ValueError('Incomplete actual backbone source members')
        for asset in inventory['license_assets']:
            path = s.regular(directory / asset['name'])
            if p.digest(path) != asset['sha256'] or path.stat().st_size != asset['bytes']: raise ValueError('Reviewed license backbone changed')
            with tarfile.open(path, 'r:') as archive:
                self.asset_members[asset['name']] = [member.name for member in archive if member.isfile()]

    def item(self, name):
        prior = self
        class Item:
            def __init__(self):
                self.name = name; self.sha256 = prior.rows[name]['sha256']; self.size = prior.rows[name]['bytes']; self.origin = prior.rows[name]['origin']
            def description(self): return prior.rows[name]
            @contextmanager
            def open(self):
                archive, member = prior.index[name]
                with archive.extractfile(member) as stream: yield stream
        return Item()

    def close(self):
        for archive in self.archives: archive.close()


def groups(entries):
    result = []; group = {}; used = 10240
    for name, item in sorted(entries.items()):
        needed = ((item.size + 511) // 512) * 512 + 4096
        if needed + 10240 > s.MAX_ASSET: raise ValueError('Single source input exceeds asset bound')
        if group and used + needed > s.MAX_ASSET:
            result.append(group); group = {}; used = 10240
        group[name] = item; used += needed
    if group: result.append(group)
    return result

def planned(entries, prefix, prior):
    old = {row['name']: row for row in prior.inventory['source_assets'] + prior.inventory['license_assets']}
    result = []
    for number, group in enumerate(groups(entries), 1):
        name = prefix + '-' + str(number).zfill(3) + '.tar'
        reusable = name in old and prior.asset_members[name] == list(group) and all(
            key in prior.rows and prior.rows[key]['sha256'] == item.sha256 and prior.rows[key]['bytes'] == item.size for key, item in group.items())
        result.append((name, group, old[name] if reusable else None))
    return result

def write_plan(plan, output, prefix, prior):
    assets = []; paths = {}
    for name, group, existing in plan:
        if existing is not None:
            assets.append(existing); paths[name] = str(prior.directory / name); continue
        temporary = output / ('.group-' + name); temporary.mkdir(mode=0o700)
        rows = s.bundles(group, temporary, prefix)
        if len(rows) != 1: raise ValueError('Deterministic source group partition changed')
        row = dict(rows[0]); source = temporary / row['name']; destination = output / name
        source.rename(destination); temporary.rmdir(); row['name'] = name
        assets.append(row); paths[name] = str(destination)
    return assets, paths


class DeltaProject(mvp.ReviewProject):
    def __init__(self, root, commit, required, entrypoints, prior, ledger):
        super().__init__(root, commit, required, {}, entrypoints)
        self.prior = prior; self.prior_ledger = ledger

    def source(self, name, expected):
        key = (name, expected)
        if key in self.cache: return self.cache[key]
        member = 'project-inputs/' + expected + '/' + name
        if self.prior.rows.get(member, {}).get('sha256') == expected:
            item = self.prior.item(member); self.cache[key] = item; return item
        if key not in self.required and key in self.prior_ledger:
            row = self.prior_ledger[key]
            if hashlib.sha256(s.git(self.repository, 'show', self.commit + ':' + name)).hexdigest() == row['current_sha256']:
                item = self.prior.item(row['included_member']); self.ledger[key] = row; self.cache[key] = item; return item
        return super().source(name, expected)


def export(args):
    root = s.ROOT
    if not isinstance(args.source_commit, str) or not accepted.release.COMMIT.fullmatch(args.source_commit):
        raise ValueError('Explicit full source Git commit required')
    if not args.plan:
        own = Path(__file__).resolve().relative_to(root).as_posix()
        if hashlib.sha256(s.git(root, 'show', args.source_commit + ':' + own)).hexdigest() != p.digest(__file__):
            raise ValueError('Actual delta producer must be committed in selected source snapshot')
    relative = args.base_acceptance.relative_to(root).as_posix()
    committed = s.git(root, 'show', 'HEAD:' + relative)
    if committed != args.base_acceptance.read_bytes(): raise ValueError('Actual committed base coordinator decision required')
    decision = p.strict(committed); base_path = s.regular(args.base_inventory); base = p.strict(base_path.read_bytes())
    if p.digest(base_path) != decision['source_inventory_sha256'] or base['kind'] != mvp.KIND:
        raise ValueError('Exact immutable reviewed export2 backbone required')
    base_artifacts = []
    for role, rows in (('source', base['source_assets']), ('licenses', base['license_assets']), ('project-source', [base['project_source']])):
        base_artifacts += [dict(row, role=role) for row in rows]
    base_artifacts.append({'role': 'inventory', 'name': base_path.name, 'sha256': p.digest(base_path), 'bytes': base_path.stat().st_size})
    base_pins = {'archive_export_sha256': base['archive_export_sha256'], 'packages': [accepted.identity(row) for row in base['packages']]}
    accepted.validate_acceptance(root, decision, base_artifacts, base_pins, base['source_commit'])
    receipt, _index = s.declarations.verified_repository(args.repository, s.metadata.public_trust())
    unchanged = changes(base['packages'], receipt['packages'])
    if s.git(root, 'merge-base', '--is-ancestor', base['source_commit'], args.source_commit) != b'': raise ValueError('Current source must preserve reviewed base ancestry')
    prior = Prior(base_path.parent, base, decision)
    try:
        # An unchanged-controller reuse is explicit, not an assertion that arbitrary new code was reviewed.
        for row in base['unresolved_historical_fingerprints']['entries']:
            if hashlib.sha256(s.git(root, 'show', args.source_commit + ':' + row['path'])).hexdigest() != row['current_sha256']:
                raise ValueError('Previously reviewed current helper changed; explicit new accounting required: ' + row['path'])
        package = next(row for row in receipt['packages'] if row['name'] == TARGET)
        subset = dict(receipt, packages=[package])
        required = installer_inputs(args.repository, package, args.records)
        _native, entrypoints, mapping = mvp.record_inputs(subset, args.records)
        old_ledger = {(row['path'], row['recorded_sha256']): row for row in base['unresolved_historical_fingerprints']['entries']}
        project = DeltaProject(root, args.source_commit, required, entrypoints, prior, old_ledger)
        entries, changed_coverage = s.collect(args.repository, subset, args.records, s.Resolver(args.source_root), project, args.npm_cache)
        for preferred_path, sha in sorted(required):
            item = project.source(preferred_path, sha); entries[item.name] = item
            changed_coverage[0]['source_members'].append(item.name)
        changed_coverage[0]['source_members'] = sorted(set(changed_coverage[0]['source_members']))
        record_path = s.regular(args.records / (TARGET + '_' + NEW_VERSION + '_' + package['architecture'] + '.json'))
        record_data = record_path.read_bytes(); record = p.strict(record_data)
        record_member = 'native-provenance/' + record_path.name
        entries[record_member] = s.Input(record_member, package['component_record_sha256'], path=record_path, origin={'kind': 'actual-native-package-record'})
        changed_coverage[0]['source_members'].append(record_member)
        # Retain actual owned public compile/reuse provenance; these are not opaque preferred-source substitutions.
        with p.tar_stream(args.repository / package['asset'], '--fsys-tarfile') as archive:
            for member in archive:
                virtual = '/' + member.name.removeprefix('./')
                if member.isfile() and virtual.startswith('/usr/share/doc/toddy-installer/native-module-') and virtual.endswith('.json'):
                    data = archive.extractfile(member).read(); sha = hashlib.sha256(data).hexdigest()
                    if member.size > 4 * 1024**2 or record['payload'][virtual]['sha256'] != sha: raise ValueError('Bounded owned installer reuse/compile provenance required')
                    name = 'package-documents/toddy-installer/' + Path(virtual).name
                    entries[name] = s.Input(name, sha, data=data, origin={'kind': 'archive-owned-original-document', 'archive_sha256': package['archive_sha256']})
                    changed_coverage[0]['source_members'].append(name)
        controls = mapping[0]
        for control in controls['declared_entrypoints']:
            item = project.cache[(control['path'], control['recorded_sha256'])]
            control.update(included_member=item.name, included_sha256=item.sha256, origin=item.origin)
        mapping_by = {row['name']: row for row in base['functional_closure']}; mapping_by[TARGET] = controls
        coverage_by = {row['name']: row for row in base['packages']}; coverage_by[TARGET] = changed_coverage[0]
        coverage = [coverage_by[row['name']] for row in receipt['packages']]
        functional = [mapping_by[row['name']] for row in receipt['packages']]
        all_entries = {name: prior.item(name) for name in prior.rows}; all_entries.update(entries)
        candidates = dict(old_ledger); candidates.update(project.ledger); needed = set()
        for row in receipt['packages']:
            path = s.regular(args.records / (row['name'] + '_' + row['version'] + '_' + row['architecture'] + '.json'))
            if p.digest(path) != row['component_record_sha256']: raise ValueError('Every current native source record must match exact new repository')
            raw = p.strict(path.read_bytes())
            for relative_path, sha in raw['supporting_build_scripts']['files'].items():
                key = ('scripts/build/' + relative_path, sha)
                if 'project-inputs/' + sha + '/' + key[0] not in all_entries:
                    if key not in candidates: raise ValueError('New unresolved script fingerprint requires accounting: ' + key[0])
                    needed.add(key)
        ledger = dict(base['unresolved_historical_fingerprints'], entries=[candidates[key] for key in sorted(needed)])
        controls['unresolved_historical_fingerprints'] = [candidates[('scripts/build/' + path, sha)] for path, sha in sorted(record['supporting_build_scripts']['files'].items()) if ('scripts/build/' + path, sha) in needed]
        for name, value in (('review/historical-fingerprints.json', ledger), ('review/functional-closure.json', functional)):
            data = p.encoded(value); all_entries[name] = s.Input(name, hashlib.sha256(data).hexdigest(), data=data, origin={'kind': 'source-review-mapping-not-qualification'})
        keep = set().union(*(set(row['source_members']) for row in coverage)) | {'review/historical-fingerprints.json', 'review/functional-closure.json'}
        # The base inventory is explicit evidence for reuse, never a scope-expansion permission.
        name = 'review/base-source-review-inventory.json'; data = base_path.read_bytes()
        all_entries[name] = s.Input(name, p.digest(base_path), data=data, origin={'kind': 'reviewed-base-source-accounting'})
        keep.add(name); all_entries = {name: item for name, item in all_entries.items() if name in keep}
        licenses = {name: item for name, item in all_entries.items() if name.startswith('package-documents/') and (name.endswith('/copyright') or '/source-notices/' in name or '/npm-supplemental-notices/' in name)}
        output = args.output
        if not output.is_absolute() or output.resolve() != output or os.path.lexists(output) or not output.parent.is_dir(): raise ValueError('Fresh private source-delta output required')
        source_plan = planned(all_entries, 'selected-sources', prior); license_plan = planned(licenses, 'source-licenses', prior)
        needed_bytes = project.bytes + sum(item.size + 4096 for plan in (source_plan, license_plan) for _name, group, reused in plan if reused is None for item in group.values()) + 64 * 1024**2
        if shutil.disk_usage(output.parent).free < s.metadata.reserve_for(output, args.capacity_scope) + needed_bytes: raise ValueError('Preserve host reserve plus complete source-delta output')
        if args.plan:
            return {'state': 'private-source-delta-plan-only', 'changed_packages': [TARGET], 'unchanged_packages': unchanged, 'preferred_input_pairs': len(required), 'required_new_output_headroom_bytes': needed_bytes, 'source_groups': [{'name': name, 'reuse_existing_path': str(prior.directory / name) if old is not None else None} for name, _group, old in source_plan], 'license_groups': [{'name': name, 'reuse_existing_path': str(prior.directory / name) if old is not None else None} for name, _group, old in license_plan], 'bundle_generated': False, 'publication_eligible': False}
        output.mkdir(mode=0o700); snapshot = output / 'toddy-project-source.tar'; project.snapshot(snapshot)
        source_assets, source_paths = write_plan(source_plan, output, 'selected-sources', prior)
        license_assets, license_paths = write_plan(license_plan, output, 'source-licenses', prior)
        value = {'version': 1, 'kind': KIND, 'source_commit': args.source_commit,
            'archive_export_sha256': p.digest(args.repository / 'archive-export.json'), 'packages': coverage,
            'members': [item.description() for _, item in sorted(all_entries.items())], 'source_assets': source_assets,
            'license_assets': license_assets, 'project_source': {'name': snapshot.name, 'sha256': p.digest(snapshot), 'bytes': snapshot.stat().st_size},
            'functional_closure': functional, 'unresolved_historical_fingerprints': ledger,
            'producer_sha256': p.digest(__file__), 'base_acceptance': {'path': relative, 'sha256': hashlib.sha256(committed).hexdigest()},
            'base_inventory_member': 'review/base-source-review-inventory.json', 'base_inventory_sha256': p.digest(base_path), 'unchanged_packages': unchanged,
            'changed_packages': [TARGET], 'source_completeness_review': 'pending', 'license_review': 'pending',
            'historical_byte_reproduction_claim': False, 'publication_eligible': False, 'signed': False, 'published': False,
            'source_urls_are_additional_only': True, 'private_cache_copied': False, 'native_runtime_qualification': False}
        with (output / 'source-review-inventory.json').open('xb') as stream: stream.write(p.encoded(value)); stream.flush(); os.fsync(stream.fileno())
        delta_accounting = {'version': 1, 'kind': 'actual-installer-source-delta-accounting', 'base_acceptance': value['base_acceptance'], 'base_inventory_sha256': value['base_inventory_sha256'], 'source_inventory_sha256': p.digest(output / 'source-review-inventory.json'), 'source_commit': args.source_commit, 'archive_export_sha256': value['archive_export_sha256'], 'unchanged_packages': [accepted.identity(row) for row in receipt['packages'] if row['name'] in unchanged], 'changed_package': dict(accepted.identity(package), declared_controllers=controls['declared_entrypoints'], source_members=changed_coverage[0]['source_members'], preferred_source_inputs=[{'path': path, 'sha256': sha} for path, sha in sorted(required)], copyright_sha256=package['copyright']['sha256'], license_basis='owner-original-license-and-retained-notices', material_and_license_decision='pending-coordinator-review'), 'historical_fingerprint_complete': False, 'publication_authorized': False}
        with (output / 'delta-accounting.json').open('xb') as stream: stream.write(p.encoded(delta_accounting)); stream.flush(); os.fsync(stream.fileno())
        artifacts = [dict(row, role='source', path=source_paths[row['name']]) for row in source_assets]
        artifacts += [dict(row, role='licenses', path=license_paths[row['name']]) for row in license_assets]
        artifacts.append(dict(value['project_source'], role='project-source', path=str(snapshot)))
        inventory_path = output / 'source-review-inventory.json'
        artifacts.append({'role': 'inventory', 'name': inventory_path.name, 'path': str(inventory_path), 'sha256': p.digest(inventory_path), 'bytes': inventory_path.stat().st_size})
        with (output / 'private-artifacts.json').open('xb') as stream: stream.write(p.encoded(artifacts)); stream.flush(); os.fsync(stream.fileno())
        fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
        return value
    finally: prior.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for option in ('base-inventory', 'base-acceptance', 'repository', 'records', 'npm-cache', 'output'):
        parser.add_argument('--' + option, type=Path, required=True)
    parser.add_argument('--source-root', action='append', default=[], type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--capacity-scope', choices=('host-export', 'native-target'), required=True)
    parser.add_argument('--plan', action='store_true', help='Verify actual changed materials and group reuse; write no bundle')
    value = export(parser.parse_args())
    print(p.encoded(value if value.get('state') == 'private-source-delta-plan-only' else {'state': KIND, 'changed_packages': value['changed_packages'], 'reused_packages': len(value['unchanged_packages']), 'publication_eligible': False}).decode(), end='')


if __name__ == '__main__': main()
