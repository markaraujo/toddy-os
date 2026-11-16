#!/usr/bin/env python3
"""Prepare private MVP source-review assets; never qualifies or publishes binaries."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import package_sources as strict

p = strict.p
OLD_NAME = 'toddy-desktop-defaults_0.2.0-1+toddy1_all'
OLD_ARCHIVE_SHA = '24b35fcc03fe9ad338109181552e55b07fb250a99942157f8945facecf125907'
OLD_RECORD_SHA = '7d40d6c20f7d8e76d8c9c344a3473c61f81ff7282ee2d53aa67dee220fff0d43'
KIND = 'native-package-source-review-draft'


def native_inputs(directory):
    directory = Path(directory)
    if directory.resolve() != directory or not directory.is_dir():
        raise ValueError('Canonical explicit recovered native inputs required')
    archive = strict.regular(directory / (OLD_NAME + '.deb'))
    record = strict.regular(directory / (OLD_NAME + '.json'))
    if p.digest(archive) != OLD_ARCHIVE_SHA or p.digest(record) != OLD_RECORD_SHA:
        raise ValueError('Exact declared previous defaults native inputs required')
    raw = p.strict(record.read_bytes())
    control, body, _size = p.archive_contents(archive)
    if (control.get('Package'), control.get('Version'), control.get('Architecture')) != ('toddy-desktop-defaults', '0.2.0-1+toddy1', 'all') or raw.get('name') != 'toddy-desktop-defaults' or raw.get('version') != '0.2.0-1+toddy1' or raw.get('installed') is not True or raw.get('archive_sha256') != OLD_ARCHIVE_SHA or raw.get('payload') != body:
        raise ValueError('Previous defaults native archive/record payload differs')
    legal = '/usr/share/doc/toddy-desktop-defaults/copyright'
    if 'sha256' not in body.get(legal, {}):
        raise ValueError('Previous defaults legal custody required')
    return {'native-inputs/' + OLD_NAME + '.deb': (archive, OLD_ARCHIVE_SHA),
            'native-inputs/' + OLD_NAME + '.json': (record, OLD_RECORD_SHA)}


def declared_original_inputs(repository, receipt, records):
    """Actual archive-owned original preferred inputs may never use replacements."""
    required = set()
    for row in receipt['packages']:
        if row['sources']:
            continue
        record = p.strict(strict.regular(Path(records) / (row['name'] + '_' + row['version'] + '_' + row['architecture'] + '.json')).read_bytes())
        wanted = 'usr/share/doc/' + row['name'] + '/source-manifest.json'
        with p.tar_stream(Path(repository) / row['asset'], '--fsys-tarfile') as stream:
            for member in stream:
                if member.isfile() and member.name.removeprefix('./') == wanted:
                    if member.size > 32 * 1024**2:
                        raise ValueError('Bounded original source manifest required')
                    data = stream.extractfile(member).read()
                    if hashlib.sha256(data).hexdigest() != record['payload'].get('/' + wanted, {}).get('sha256'):
                        raise ValueError('Original source manifest native ownership differs')
                    manifest = p.strict(data)
                    for name, value in manifest.get('source_inputs', manifest.get('inputs', {})).items():
                        required.add((name, value['sha256'] if isinstance(value, dict) else value))
    return required


class ReviewProject:
    def __init__(self, repository, commit, required, external, entrypoints):
        self.exact = strict.Project(repository, commit)
        self.repository = self.exact.repository
        self.commit = commit
        self.bytes = self.exact.bytes
        self.required = required
        self.external = external
        self.entrypoints = entrypoints
        self.cache = {}
        self.ledger = {}

    def snapshot(self, output):
        return self.exact.snapshot(output)

    def source(self, name, expected):
        key = (name, expected)
        if key in self.cache:
            return self.cache[key]
        if name.startswith('native-inputs/'):
            if name not in self.external or self.external[name][1] != expected or key not in self.required:
                raise ValueError('Only exact declared previous defaults build inputs allowed')
            path, sha = self.external[name]
            result = strict.Input('native-build-inputs/' + name.removeprefix('native-inputs/'), sha,
                path=path, origin={'kind': 'declared-native-build-input', 'declared_path': name})
        else:
            try:
                result = self.exact.source(name, expected)
            except ValueError:
                # Original preferred source inputs are exact even in this draft.
                if key in self.required or not name.startswith('scripts/build/'):
                    raise
                strict.relative(name)
                if not p.HASH.fullmatch(expected):
                    raise ValueError('Actual historical script hash required')
                row = {'path': name, 'recorded_sha256': expected,
                    'declared_entrypoint': key in self.entrypoints,
                    'necessity_review': 'pending', 'historical_bytes_recovered': False}
                try:
                    data = strict.git(self.repository, 'show', self.commit + ':' + name)
                except strict.subprocess.CalledProcessError:
                    data = None
                if data is None:
                    if key in self.entrypoints:
                        raise ValueError('Missing both historical and current declared build entrypoint: ' + name)
                    row.update(status='missing-current-path', current_sha256=None, included_member=None)
                    encoded = p.encoded(row)
                    result = strict.Input('unresolved-historical-fingerprints/' + expected + '/' + name + '.json',
                        hashlib.sha256(encoded).hexdigest(), data=encoded,
                        origin={'kind': 'unresolved-fingerprint-ledger-not-source', 'declared_path': name})
                else:
                    sha = hashlib.sha256(data).hexdigest()
                    member = 'current-build-scripts/' + sha + '/' + name
                    row.update(status='current-script-included', current_sha256=sha, included_member=member)
                    result = strict.Input(member, sha, data=data,
                        origin={'kind': 'current-functional-script-review-required', 'commit': self.commit,
                            'path': name})
                self.ledger[key] = row
        self.cache[key] = result
        return result


def record_inputs(receipt, records):
    inputs = {}
    entrypoints = set()
    mapping = []
    for row in receipt['packages']:
        filename = row['name'] + '_' + row['version'] + '_' + row['architecture'] + '.json'
        path = strict.regular(Path(records) / filename)
        if p.digest(path) != row['component_record_sha256']:
            raise ValueError('Exact selected native provenance record required')
        raw = p.strict(path.read_bytes())
        inputs['native-provenance/' + filename] = strict.Input('native-provenance/' + filename,
            row['component_record_sha256'], path=path, origin={'kind': 'actual-native-package-record'})
        fields = raw['supporting_build_scripts']['files']
        controls = []
        for name, sha in fields.items():
            roles = [field for field in ('recipe_sha256', 'packager_sha256') if raw.get(field) == sha]
            if roles:
                entrypoints.add(('scripts/build/' + name, sha))
                controls.append({'path': 'scripts/build/' + name, 'recorded_sha256': sha, 'roles': roles})
        if not all(any(field in item['roles'] for item in controls) for field in ('recipe_sha256', 'packager_sha256')):
            raise ValueError('Recorded recipe and packager identity required')
        mapping.append({'name': row['name'], 'version': row['version'], 'architecture': row['architecture'],
            'provenance_member': 'native-provenance/' + filename,
            'declared_entrypoints': controls, 'controlling_script_review': 'pending',
            'unresolved_historical_fingerprints': []})
    return inputs, entrypoints, mapping


def export(args):
    receipt, _index = strict.declarations.verified_repository(args.repository, strict.metadata.public_trust())
    required = declared_original_inputs(args.repository, receipt, args.records)
    external = native_inputs(args.native_build_inputs)
    records, entrypoints, mapping = record_inputs(receipt, args.records)
    project = ReviewProject(strict.ROOT, args.source_commit, required, external, entrypoints)
    resolver = strict.Resolver(args.source_root, args.foundation_source_tar)
    entries, coverage = strict.collect(args.repository, receipt, args.records, resolver, project,
        args.npm_cache, args.generated_catalog_attestation, args.generated_catalog_projection)
    # Current functional declarations must preserve every covered frozen version.
    source = strict.git(strict.ROOT, 'show', args.source_commit + ':scripts/build/phase2/install_verified_stage.py')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PROFILES' for t in n.targets))
    profiles = ast.literal_eval(node.value)
    for row in mapping:
        if row['name'] in profiles:
            upstream = profiles[row['name']][0]
            if not row['version'].startswith(upstream + '-'):
                raise ValueError('Current functional profile changes a frozen upstream version')
            row['current_profile_upstream_version'] = upstream
        raw = p.strict((Path(args.records) / (row['name'] + '_' + row['version'] + '_' + row['architecture'] + '.json')).read_bytes())
        row['unresolved_historical_fingerprints'] = [project.ledger[('scripts/build/' + name, sha)]
            for name, sha in sorted(raw['supporting_build_scripts']['files'].items()) if ('scripts/build/' + name, sha) in project.ledger]
    entries.update(records)
    for row in coverage:
        member = 'native-provenance/' + row['name'] + '_' + row['version'] + '_' + row['architecture'] + '.json'
        row['source_members'] = sorted(set(row['source_members']) | {member})
    for row in mapping:
        for control in row['declared_entrypoints']:
            item = project.cache.get((control['path'], control['recorded_sha256']))
            if item is None:
                raise ValueError('Every declared build entrypoint must be included')
            control.update(included_member=item.name, included_sha256=item.sha256, origin=item.origin)
    ledger = {'version': 1, 'kind': 'unresolved-historical-fingerprint-review-ledger',
        'entries': [row for _, row in sorted(project.ledger.items())], 'necessity_review': 'pending'}
    for name, value in (('review/historical-fingerprints.json', ledger), ('review/functional-closure.json', mapping)):
        data = p.encoded(value)
        entries[name] = strict.Input(name, hashlib.sha256(data).hexdigest(), data=data,
            origin={'kind': 'source-review-mapping-not-qualification'})
    output = args.output
    if not output.is_absolute() or output.resolve() != output or os.path.lexists(output) or not output.parent.is_dir():
        raise ValueError('Fresh canonical private review output required')
    licenses = {name: item for name, item in entries.items() if name.startswith('package-documents/') and (name.endswith('/copyright') or '/source-notices/' in name or '/npm-supplemental-notices/' in name)}
    needed = project.bytes + sum(x.size + 4096 for x in entries.values()) + sum(x.size + 4096 for x in licenses.values()) + 64 * 1024**2
    if shutil.disk_usage(output.parent).free < strict.metadata.reserve_for(output, args.capacity_scope) + needed:
        raise ValueError('Preserve source-review capacity reserve')
    output.mkdir(mode=0o700)
    project_path = output / 'toddy-project-source.tar'
    project.snapshot(project_path)
    source_assets = strict.bundles(entries, output)
    license_assets = strict.bundles(licenses, output, 'source-licenses')
    inventory = {'version': 1, 'kind': KIND, 'source_commit': args.source_commit,
        'archive_export_sha256': p.digest(args.repository / 'archive-export.json'), 'packages': coverage,
        'members': [item.description() for _, item in sorted(entries.items())],
        'source_assets': source_assets, 'license_assets': license_assets,
        'project_source': {'name': project_path.name, 'sha256': p.digest(project_path), 'bytes': project_path.stat().st_size},
        'producer_sha256': p.digest(__file__), 'strict_producer_sha256': p.digest(strict.__file__),
        'functional_closure': mapping, 'unresolved_historical_fingerprints': ledger,
        'source_completeness_review': 'pending', 'license_review': 'pending',
        'historical_byte_reproduction_claim': False, 'publication_eligible': False,
        'source_urls_are_additional_only': True, 'private_cache_copied': False,
        'signed': False, 'published': False, 'native_runtime_qualification': False}
    with (output / 'source-review-inventory.json').open('xb') as stream:
        stream.write(p.encoded(inventory)); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ('repository', 'records', 'npm-cache', 'native-build-inputs', 'generated-catalog-attestation', 'generated-catalog-projection', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--source-root', action='append', default=[], type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--foundation-source-tar', type=Path)
    parser.add_argument('--capacity-scope', choices=('host-export', 'native-target'), required=True)
    args = parser.parse_args()
    value = export(args)
    print(json.dumps({'state': KIND, 'packages': len(value['packages']), 'source_assets': len(value['source_assets']),
        'unresolved_historical_fingerprints': len(value['unresolved_historical_fingerprints']['entries']),
        'publication_eligible': False, 'license_review': 'pending'}))


if __name__ == '__main__':
    main()
