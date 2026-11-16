#!/usr/bin/env python3
"""Independent current-functional source admission; immutable drafts stay drafts."""
import argparse
import ast
import base64
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import re
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]
import package_sources as strict
import package_sources_mvp as mvp
import phase2_release as release

p = strict.p
KIND = 'current-functional-source-review-acceptance'
DECISION = 'accepted-for-experimental-source-publication'
DELTA_KIND = 'native-package-source-review-delta-draft'
CONDITIONS = ['retain-exact-public-sources-and-notices', 'retain-historical-fingerprint-ledger', 'no-historical-binary-or-g2-claim']
IDENTITY = ('name', 'version', 'architecture', 'archive_sha256', 'component_record_sha256', 'recipe_sha256')


def identity(row):
    return {key: row[key] for key in IDENTITY}


def digest_value(value):
    return hashlib.sha256(p.encoded(value)).hexdigest()


def validate_acceptance(root, review, artifacts, pins, commit):
    """Validate actual committed coordinator decisions, including on portal read."""
    keys = {'version', 'kind', 'decision', 'archive_export_sha256', 'source_inventory_sha256', 'source_commit',
        'technical_review', 'assets', 'packages', 'historical_fingerprint_complete',
        'historical_fingerprint_ledger_sha256', 'historical_binary_reproduction_claim',
        'native_runtime_or_g2_acceptance', 'reviewer', 'reviewed_at_utc'}
    if not isinstance(review, dict) or set(review) != keys or type(review['version']) is not int or review['version'] != 1 or review['kind'] != KIND or review['decision'] != DECISION:
        raise ValueError('Actual typed coordinator source acceptance required')
    if review['source_commit'] != commit or review['archive_export_sha256'] != pins['archive_export_sha256'] or any(review[key] is not False for key in ('historical_fingerprint_complete', 'historical_binary_reproduction_claim', 'native_runtime_or_g2_acceptance')):
        raise ValueError('Exact source scope and truthful historical/runtime limitations required')
    if not isinstance(review['reviewer'], str) or not review['reviewer'].strip() or not isinstance(review['reviewed_at_utc'], str):
        raise ValueError('Actual coordinator identity and UTC review time required')
    try:
        moment = datetime.fromisoformat(review['reviewed_at_utc'].replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Actual UTC source review time required') from error
    if moment.utcoffset() != timedelta(0):
        raise ValueError('Actual UTC source review time required')
    reference = review['technical_review']
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
        raise ValueError('Exact committed technical accounting reference required')
    report = release.evidence(root, reference['path'], reference['sha256'])
    if report.get('source_commit') != commit or report.get('archive_export_sha256') != pins['archive_export_sha256'] or report.get('source_inventory_sha256') != review['source_inventory_sha256'] or report.get('actual_missing_source_materials') != [] or report.get('historical_fingerprint_complete') is not False:
        raise ValueError('Technical accounting must match exact sources with no required material gap')
    selected = sorted([{key: row[key] for key in ('name', 'sha256', 'bytes')} for row in artifacts
        if row['role'] in ('source', 'licenses', 'project-source', 'inventory')], key=lambda row: row['name'])
    if review['assets'] != selected:
        raise ValueError('Every actual source/license/project/inventory asset must be reviewed')
    inventory_rows = [row for row in artifacts if row['role'] == 'inventory']
    if len(inventory_rows) != 1 or inventory_rows[0]['sha256'] != review['source_inventory_sha256']:
        raise ValueError('Reviewed source inventory asset differs')
    reports = report['packages']
    if len(review['packages']) != len(pins['packages']) or len(reports) != len(pins['packages']):
        raise ValueError('Every exact native package requires individual material/license decisions')
    for approved, package, technical in zip(review['packages'], pins['packages'], reports):
        expected = set(IDENTITY) | {'technical_row_sha256', 'material_decision', 'license_decision', 'license_basis', 'conditions'}
        if set(approved) != expected or identity(approved) != package or any(technical[key] != package[key] for key in ('name', 'version', 'architecture', 'archive_sha256', 'component_record_sha256')):
            raise ValueError('Coordinator decision package identity differs')
        if approved['technical_row_sha256'] != digest_value(technical) or approved['material_decision'] != 'accepted' or approved['license_decision'] != 'accepted' or approved['license_basis'] != technical['license_accounting_basis'] or approved['conditions'] != CONDITIONS:
            raise ValueError('Actual package-specific material/license decision and conditions required')
    return report


class Materials:
    def __init__(self, inventory, artifacts):
        self.inventory = inventory
        self.wanted = {row['path']: row for row in inventory['members']}
        self.archives = []
        self.index = {}
        if len(self.wanted) != len(inventory['members']) or not self.wanted:
            raise ValueError('Unique actual source member accounting required')
        by_name = {row['name']: row for row in artifacts}
        try:
            for field in ('source_assets', 'license_assets'):
                expected = self.wanted if field == 'source_assets' else {name: row for name, row in self.wanted.items()
                    if name.startswith('package-documents/') and (name.endswith('/copyright') or '/source-notices/' in name or '/npm-supplemental-notices/' in name)}
                seen = set()
                for asset in inventory[field]:
                    path = strict.regular(by_name[asset['name']]['path'])
                    if path.stat().st_size != asset['bytes'] or path.stat().st_size > strict.MAX_ASSET or p.digest(path) != asset['sha256']:
                        raise ValueError('Reviewed actual source tar identity differs')
                    archive = tarfile.open(path, 'r:'); self.archives.append(archive)
                    for member in archive:
                        p.canonical(member.name, absolute=False)
                        if member.name in seen or member.name not in expected or not member.isfile() or (member.uid, member.gid, member.mode, member.mtime) != (0, 0, 0o644, 0):
                            raise ValueError('Unsafe, extra or duplicate reviewed source member')
                        with archive.extractfile(member) as stream:
                            actual = strict.hash_stream(stream)
                        row = expected[member.name]
                        if actual != (row['sha256'], row['bytes']):
                            raise ValueError('Reviewed source member hash/size differs')
                        seen.add(member.name)
                        if field == 'source_assets': self.index[member.name] = (archive, member)
                if seen != set(expected):
                    raise ValueError('Incomplete reviewed source/license contents')
        except BaseException:
            self.close(); raise

    def read(self, name, maximum=128 * 1024**2):
        if name not in self.index or self.wanted[name]['bytes'] > maximum:
            raise ValueError('Required bounded actual source member missing: ' + name)
        archive, member = self.index[name]
        return archive.extractfile(member).read()

    def close(self):
        for archive in self.archives: archive.close()


def verify_project(root, commit, inventory, artifacts):
    project = strict.Project(root, commit)
    asset = inventory['project_source']; by_name = {row['name']: row for row in artifacts}
    path = strict.regular(by_name[asset['name']]['path'])
    if p.digest(path) != asset['sha256'] or path.stat().st_size != asset['bytes'] or path.stat().st_size > strict.MAX_ASSET:
        raise ValueError('Reviewed current project snapshot differs')
    seen = set()
    with tarfile.open(path, 'r:') as archive:
        if archive.pax_headers.get('comment') != commit:
            raise ValueError('Exact current-functional Git snapshot required')
        for member in archive:
            if member.isdir(): continue
            if not member.name.startswith('toddy-project/'):
                raise ValueError('Foreign project snapshot namespace')
            name = strict.relative(member.name[len('toddy-project/'):])
            if name in seen or name not in project.paths:
                raise ValueError('Extra/duplicate project source member')
            data = member.linkname.encode() if member.issym() else archive.extractfile(member).read() if member.isfile() else None
            if data != strict.git(root, 'show', commit + ':' + name):
                raise ValueError('Current project source differs from actual Git commit')
            seen.add(name)
    if seen != set(project.paths): raise ValueError('Incomplete current project snapshot')


def verify_delta_backbone(root, inventory, material, receipt, report):
    """Reuse only byte-identical reviewed members for unchanged native identities."""
    from package_sources_delta import changes
    reference = inventory['base_acceptance']
    if set(reference) != {'path', 'sha256'}: raise ValueError('Exact committed base source decision required')
    decision = release.evidence(root, reference['path'], reference['sha256'])
    data = material.read(inventory['base_inventory_member'])
    if hashlib.sha256(data).hexdigest() != inventory['base_inventory_sha256'] or inventory['base_inventory_sha256'] != decision['source_inventory_sha256']:
        raise ValueError('Immutable reviewed base inventory differs')
    base = p.strict(data)
    if base.get('kind') != mvp.KIND: raise ValueError('Only directly reviewed export2 backbone supported')
    artifacts = []
    for role, assets in (('source', base['source_assets']), ('licenses', base['license_assets']), ('project-source', [base['project_source']])):
        artifacts += [dict(row, role=role) for row in assets]
    artifacts.append({'role': 'inventory', 'name': 'source-review-inventory.json', 'sha256': inventory['base_inventory_sha256'], 'bytes': len(data)})
    pins = {'archive_export_sha256': base['archive_export_sha256'], 'packages': [identity(row) for row in base['packages']]}
    previous_report = validate_acceptance(root, decision, artifacts, pins, base['source_commit'])
    unchanged = changes(base['packages'], receipt['packages'])
    if inventory['unchanged_packages'] != unchanged or inventory['changed_packages'] != ['toddy-installer']:
        raise ValueError('Changed source scope must be explicitly installer1 to installer4 only')
    if strict.git(root, 'merge-base', '--is-ancestor', base['source_commit'], inventory['source_commit']) != b'':
        raise ValueError('Current source must preserve actual reviewed backbone ancestry')
    old_coverage = {row['name']: row for row in base['packages']}; coverage = {row['name']: row for row in inventory['packages']}
    old_members = {row['path']: row for row in base['members']}; old_rows = {row['name']: row for row in previous_report['packages']}; rows = {row['name']: row for row in report['packages']}
    old_controls = {row['name']: row for row in base['functional_closure']}; controls = {row['name']: row for row in inventory['functional_closure']}
    for name in unchanged:
        if coverage[name] != old_coverage[name] or controls[name] != old_controls[name] or digest_value(rows[name]) != digest_value(old_rows[name]):
            raise ValueError('Unchanged package evidence requires exact prior coverage/control/technical row')
        for member in coverage[name]['source_members']:
            if material.wanted.get(member) != old_members.get(member):
                raise ValueError('Reused package material member changed')
    return set(unchanged)


def verify_assets(root, inventory_path, artifacts, pins, commit, review, repository):
    report = validate_acceptance(root, review, artifacts, pins, commit)
    inventory_path = strict.regular(inventory_path)
    inventory = p.strict(inventory_path.read_bytes())
    if p.digest(inventory_path) != review['source_inventory_sha256'] or inventory.get('kind') not in (mvp.KIND, DELTA_KIND) or inventory.get('source_commit') != commit or inventory.get('archive_export_sha256') != pins['archive_export_sha256'] or inventory.get('publication_eligible') is not False or inventory.get('signed') is not False or inventory.get('published') is not False or inventory.get('historical_byte_reproduction_claim') is not False:
        raise ValueError('Original immutable reviewed draft inventory required')
    producer_fields = (('producer_sha256', 'scripts/build/phase2/package_sources_delta.py'),) if inventory['kind'] == DELTA_KIND else (('producer_sha256', 'scripts/build/phase2/package_sources_mvp.py'), ('strict_producer_sha256', 'scripts/build/phase2/package_sources.py'))
    for field, relative in producer_fields:
        if inventory.get(field) != hashlib.sha256(strict.git(root, 'show', commit + ':' + relative)).hexdigest():
            raise ValueError('Actual source producer identity differs from source snapshot')
    if [identity(row) for row in inventory['packages']] != pins['packages']:
        raise ValueError('Reviewed source package scope differs; changed packages require new accounting')
    for role, expected in (('source', inventory['source_assets']), ('licenses', inventory['license_assets']), ('project-source', [inventory['project_source']])):
        if [{key: row[key] for key in ('name', 'sha256', 'bytes')} for row in artifacts if row['role'] == role] != expected:
            raise ValueError('Actual reviewed asset roles/order differ')
    receipt, _index = strict.declarations.verified_repository(repository, strict.metadata.public_trust())
    if p.digest(Path(repository) / 'archive-export.json') != pins['archive_export_sha256'] or [identity(row) for row in receipt['packages']] != pins['packages']:
        raise ValueError('Current signed repository scope differs from reviewed materials')
    verify_project(root, commit, inventory, artifacts)
    profile_source = strict.git(root, 'show', commit + ':scripts/build/phase2/install_verified_stage.py')
    profile_node = next(node for node in ast.parse(profile_source).body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'PROFILES' for target in node.targets))
    profiles = ast.literal_eval(profile_node.value)
    for package in receipt['packages']:
        if package['name'] in profiles and not package['version'].startswith(profiles[package['name']][0] + '-'):
            raise ValueError('Reviewed current profile changes a selected frozen upstream version')
    material = Materials(inventory, artifacts)
    try:
        ledger = inventory['unresolved_historical_fingerprints']
        if digest_value(ledger) != review['historical_fingerprint_ledger_sha256']:
            raise ValueError('Historical fingerprint ledger must remain unchanged')
        ledger_rows = {(row['path'], row['recorded_sha256']): row for row in ledger['entries']}
        if len(ledger_rows) != len(ledger['entries']): raise ValueError('Duplicate historical fingerprint')
        if p.strict(material.read('review/historical-fingerprints.json')) != ledger or p.strict(material.read('review/functional-closure.json')) != inventory['functional_closure']:
            raise ValueError('Actual review mapping/ledger bytes differ')
        current_rows = {row['name']: row for row in inventory['functional_closure']}
        reused = verify_delta_backbone(root, inventory, material, receipt, report) if inventory['kind'] == DELTA_KIND else set()
        actual_missing = set(); covered = set()
        for package, coverage in zip(receipt['packages'], inventory['packages']):
            name = package['name']; prefix = 'package-documents/' + name + '/'
            record_member = 'native-provenance/' + name + '_' + package['version'] + '_' + package['architecture'] + '.json'
            record_data = material.read(record_member)
            if hashlib.sha256(record_data).hexdigest() != package['component_record_sha256']:
                raise ValueError('Actual native source provenance record differs')
            record = p.strict(record_data)
            if name not in reused:
                control, body, _size = p.archive_contents(strict.regular(Path(repository) / package['asset']))
                if record['payload'] != body or record['archive_sha256'] != package['archive_sha256'] or (control.get('Package'), control.get('Version'), control.get('Architecture')) != (name, package['version'], package['architecture']):
                    raise ValueError('Native archive/control/provenance chain differs')
                documents = {}
                for path, row in material.wanted.items():
                    if not path.startswith(prefix): continue
                    local = path[len(prefix):]
                    virtual = strict.generated_voice.CATALOG if name == strict.generated_voice.bridge.PACKAGE and local == 'catalog.json' else '/usr/share/doc/' + name + '/' + local
                    if body.get(virtual, {}).get('sha256') != row['sha256']:
                        raise ValueError('Original source/license document differs from native archive')
                    documents[local] = material.read(path)
                if hashlib.sha256(documents['copyright']).hexdigest() != package['copyright']['sha256']:
                    raise ValueError('Required actual copyright differs')
                if package['source_notices_index']:
                    value = p.strict(documents['source-notices/index.json'])
                    for source in value['sources']:
                        for notice in source['notices']:
                            data = documents['source-notices/' + notice['sha256']]
                            if len(data) != notice['size'] or hashlib.sha256(data).hexdigest() != notice['sha256']:
                                raise ValueError('Actual retained notice chain differs')
                for source in package['sources']:
                    member = 'upstream/' + source['sha256'] + '/' + source['filename']
                    if material.wanted.get(member, {}).get('sha256') != source['sha256']:
                        raise ValueError('Selected preferred upstream source missing')
                preferred = p.strict(documents['source-manifest.json']) if 'source-manifest.json' in documents else None
                if preferred and (not package['sources'] or (inventory['kind'] == DELTA_KIND and name == 'toddy-installer')):
                    for path, value in preferred.get('source_inputs', preferred.get('inputs', {})).items():
                        expected = value['sha256'] if isinstance(value, dict) else value
                        if path.startswith('native-inputs/'):
                            allowed = {'native-inputs/' + mvp.OLD_NAME + '.deb': mvp.OLD_ARCHIVE_SHA, 'native-inputs/' + mvp.OLD_NAME + '.json': mvp.OLD_RECORD_SHA}
                            if allowed.get(path) != expected: raise ValueError('Unreviewed external native build input')
                            member = 'native-build-inputs/' + path[len('native-inputs/'):]
                        else:
                            strict.relative(path); member = 'project-inputs/' + expected + '/' + path
                        if material.wanted.get(member, {}).get('sha256') != expected:
                            raise ValueError('Original preferred source/native build input missing: ' + name + ' ' + path)
                if name == 'toddy-agent':
                    custody = p.strict(documents['npm-custody.json']); distinct = set()
                    if len(custody['components']) != 88: raise ValueError('Complete audited NPM locations required')
                    for component in custody['components']:
                        data = material.read('npm/' + component['archive_sha256'] + '.tgz')
                        if len(data) != component['archive_bytes'] or hashlib.sha512(data).digest() != base64.b64decode(component['integrity'].split('-', 1)[1], validate=True):
                            raise ValueError('Audited NPM preferred distribution bytes differ')
                        distinct.add(component['archive_sha256'])
                    if len(distinct) != 87: raise ValueError('Complete distinct NPM archive closure required')
                if name == strict.generated_voice.bridge.PACKAGE:
                    strict.generated_voice.verify(package, record, documents,
                        p.strict(material.read('builder-export/voice-native2-attestation.json')),
                        p.strict(material.read('builder-export/voice-native2-projection.json')))
            for relative, expected in record['supporting_build_scripts']['files'].items():
                path = 'scripts/build/' + relative; exact = 'project-inputs/' + expected + '/' + path
                if material.wanted.get(exact, {}).get('sha256') == expected: continue
                key = (path, expected); actual_missing.add(key)
                if key not in ledger_rows: raise ValueError('Unaccounted historical script fingerprint')
                row = ledger_rows[key]; member = row['included_member']
                if row['status'] != 'current-script-included' or material.wanted.get(member, {}).get('sha256') != row['current_sha256'] or material.read(member) != strict.git(root, 'show', commit + ':' + path):
                    raise ValueError('Actual current functional script replacement missing')
            for entry in current_rows[name]['declared_entrypoints']:
                if entry['recorded_sha256'] not in (record['recipe_sha256'], record['packager_sha256']) or material.wanted.get(entry['included_member'], {}).get('sha256') != entry['included_sha256']:
                    raise ValueError('Declared source controller missing or not native-bound')
            if not coverage['source_members'] or not set(coverage['source_members']) <= set(material.wanted): raise ValueError('Missing actual package source member')
            covered.update(coverage['source_members'])
        if actual_missing != set(ledger_rows): raise ValueError('Historical ledger omitted or invented a fingerprint')
        expected_extra = {'review/historical-fingerprints.json', 'review/functional-closure.json'} | ({inventory['base_inventory_member']} if inventory['kind'] == DELTA_KIND else set())
        if set(material.wanted) - covered != expected_extra:
            raise ValueError('Unexpected unaccounted source material')
        with tempfile.TemporaryDirectory(prefix='toddy-reviewed-native-inputs-') as directory:
            destination = Path(directory)
            for suffix in ('.deb', '.json'):
                filename = mvp.OLD_NAME + suffix
                (destination / filename).write_bytes(material.read('native-build-inputs/' + filename))
            mvp.native_inputs(destination)
    finally:
        material.close()
    return {'mode': 'current-functional-coordinator-reviewed', 'packages': len(inventory['packages']),
        'historical_fingerprint_complete': False, 'native_runtime_or_g2_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--acceptance', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, help='Private typed role/path manifest for exact reused source assets')
    args = parser.parse_args(); root = strict.ROOT
    relative = args.acceptance.relative_to(root).as_posix()
    raw = strict.git(root, 'show', 'HEAD:' + relative)
    if args.acceptance.read_bytes() != raw: raise ValueError('Actual committed coordinator decision required')
    review = p.strict(raw); inventory = p.strict(args.inventory.read_bytes())
    receipt, _index = strict.declarations.verified_repository(args.repository, strict.metadata.public_trust())
    pins = {'archive_export_sha256': p.digest(args.repository / 'archive-export.json'), 'packages': [identity(row) for row in receipt['packages']]}
    artifacts = []
    for role, assets in (('source', inventory['source_assets']), ('licenses', inventory['license_assets']), ('project-source', [inventory['project_source']])):
        artifacts += [dict(row, role=role, path=str(args.inventory.parent / row['name'])) for row in assets]
    artifacts.append({'role': 'inventory', 'name': args.inventory.name, 'sha256': p.digest(args.inventory), 'bytes': args.inventory.stat().st_size, 'path': str(args.inventory)})
    if args.artifacts:
        supplied = p.strict(strict.regular(args.artifacts).read_bytes())
        if not isinstance(supplied, list) or len({row.get('name') for row in supplied}) != len(supplied) or any(set(row) != {'role', 'name', 'path', 'sha256', 'bytes'} or row['role'] not in ('source', 'licenses', 'project-source', 'inventory') for row in supplied):
            raise ValueError('Exact private source artifact role/path list required')
        artifacts = supplied
    print(p.encoded(verify_assets(root, args.inventory, artifacts, pins, inventory['source_commit'], review, args.repository)).decode(), end='')


if __name__ == '__main__': main()
