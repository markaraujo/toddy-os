#!/usr/bin/env python3
"""Export verified installed native component/source records; no release claim.

Run inside the guarded disposable builder. Output contains no private keys,
archives or workstation paths. This is a partial inventory until the final
base ownership/dependency/license audits and release gates actually pass.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TARGET = Path('/mnt/lfs')
CACHE = Path('/var/cache/toddy/packages')
RECORDS = Path('/var/log/toddy/packages')


def collect(target=TARGET, source_root=TARGET):
    output = subprocess.check_output(['dpkg-query', '--admindir=' + str(target / 'var/lib/dpkg'),
                                      '-W', '-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'], text=True)
    installed = {}
    for line in output.splitlines():
        name, version, architecture, status = line.split('\t')
        if status == 'install ok installed':
            installed[name] = (version, architecture)
    hashes = {}

    def digest(path):
        if path not in hashes:
            with path.open('rb') as stream:
                hashes[path] = hashlib.file_digest(stream, 'sha256').hexdigest()
        return hashes[path]

    license_rows = json.loads((HERE.parents[1]/'config/component-licenses.json').read_text())['components']
    components = []
    for name, (version, architecture) in sorted(installed.items()):
        archive = f'{name}_{version}_{architecture}.deb'
        metadata = RECORDS / (archive.removesuffix('.deb') + '.json')
        record = json.loads(metadata.read_text())
        if not record['installed'] or record['name'] != name or record['version'] != version:
            raise SystemExit(f'Installed package provenance mismatch: {name}')
        if digest(CACHE / archive) != record['archive_sha256']:
            raise SystemExit(f'Native package archive corruption: {name}')
        for source in record['sources']:
            if digest(source_root / 'sources' / source['filename']) != source['sha256']:
                raise SystemExit(f'Corresponding source corruption: {source["filename"]}')
        notice = '/usr/share/doc/' + name + '/copyright'
        notice_hash = digest(target / notice.lstrip('/'))
        if notice_hash != record['payload'][notice]['sha256']:
            raise SystemExit(f'Installed copyright notice mismatch: {name}')
        baseline=re.sub(r'\+toddy[1-9][0-9]*$','',version)
        reviewed = next((r for r in license_rows if r['name'] == name and (baseline == r['version'] or baseline.startswith(r['version']+'-'))), None)
        components.append({'name': name, 'version': version, 'architecture': architecture,
                           'archive': archive, 'archive_sha256': record['archive_sha256'],
                           'component_record_sha256': digest(metadata),
                           'recipe_sha256': record['recipe_sha256'],
                           'supporting_recipe_set_sha256': record.get('supporting_build_scripts', {}).get('sha256'),
                           'sources': record['sources'], 'copyright_path': notice,
                           'copyright_sha256': notice_hash,
                           'runtime_dependency_closure': record.get('runtime_dependency_closure',
                               'not recorded in early metadata; final audit required'),
                           'packaging_backend': record.get('packaging_backend', {'kind':'builder-bootstrap-dpkg'}),
                           'book_sources': record.get('book_sources'),
                           'source_kind': record.get('source_kind', 'upstream-archives-and-versioned-recipe'),
                           'license_expression': reviewed['license'] if reviewed else 'pending final license inventory review',
                           'license_review': reviewed})
    return {'schema_version': 1, 'scope': 'installed native packages only',
                      'release_complete': False, 'generated_at': datetime.now(timezone.utc).isoformat(),
                      'package_count': len(components), 'components': components}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, help='H11 assembled image package set; sources remain in the guarded builder')
    args = parser.parse_args()
    subprocess.run(['bash', '-c', 'source "$1"; guard_target', 'guard',
                    str(HERE / 'target.sh')], check=True)
    target = TARGET
    if args.image is not None:
        subprocess.run(['python3', str(HERE / 'h11/require_gate.py')], check=True)
        import sys
        sys.path.insert(0, str(HERE / 'h10'))
        from initramfs_input import physical
        target = physical(TARGET, args.image, directory=True)
    print(json.dumps(collect(target, TARGET), indent=2))


if __name__ == '__main__':
    main()
