#!/usr/bin/env python3
"""Bind a verified local foundation export to its clean committed source revision."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    directory = args.directory.absolute()
    if directory.resolve() != directory or not directory.is_relative_to(ROOT / '.local/releases'):
        raise ValueError('Use a physical project-local release directory')
    state = json.loads((ROOT / 'status.json').read_text())
    if state['gates']['G1'] != 'passed' or any(row['status'] != 'not_started'
            for row in state['milestones'] if row['id'].startswith('B')):
        raise ValueError('Require accepted foundation and unstarted Phase 2')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise ValueError('Commit reviewed delivery inputs first')
    review = json.loads((ROOT / 'docs/evidence/H13-export.json').read_text())
    if not review['complete'] or review['directory'] != str(directory.relative_to(ROOT)):
        raise ValueError('Export does not match the reviewed local delivery')
    expected = dict(review['artifacts'])
    expected['native-build-evidence.tar.gz'] = review['native_build_evidence']
    expected['test-evidence.tar.gz'] = review['test_evidence']
    for name, record in expected.items():
        path = directory / name
        if path.resolve() != path or path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
            raise ValueError('Changed delivery input: ' + name)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    bundle = directory / 'toddy-source-history.bundle'
    if not bundle.exists():
        subprocess.run(['git', 'bundle', 'create', str(bundle), 'HEAD'], cwd=ROOT, check=True)
    subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=ROOT, check=True)
    heads = subprocess.check_output(['git', 'bundle', 'list-heads', str(bundle)], text=True).splitlines()
    if heads != [revision + ' HEAD']:
        raise ValueError('Preserve the old source bundle before finalizing a new revision')
    (directory / 'START-HERE.txt').write_text(
        'Toddy OS experimental command-line foundation — local owner testing\n'
        'G1 passed in QEMU/KVM. Physical hardware remains pending.\n'
        'No graphical desktop, agent or installer is included in this phase.\n'
        'Verify every delivered file: sha256sum -c SHA256SUMS\n'
        'Recover the committed instructions without network access:\n'
        '  git clone toddy-source-history.bundle toddy-source\n'
        '  cd toddy-source\n'
        'Read docs/FOUNDATION-TESTING.md for the isolated VM command and limits.\n'
        'Point its toddy_iso variable to the sibling delivered ISO when using this clone.\n'
        'Read docs/FRESH-BUILD.md and docs/RECOVERY.md for build/recovery.\n'
        'Source archives include corresponding image inputs; host/book inputs use frozen locks.\n'
        'Native build and test archives each contain a member SHA-256 manifest.\n'
        'Third-party licenses remain in components.json and native-build-evidence.tar.gz.\n'
        'Original-project licensing remains pending before public binary redistribution.\n'
        'B01-B13 await explicit owner approval after testing.\n'
        'Source revision: ' + revision + '\n')
    artifacts = {}
    for path in sorted(directory.iterdir()):
        if path.name in ('release-summary.json', 'SHA256SUMS'):
            continue
        if path.resolve() != path or not path.is_file():
            raise ValueError('Unexpected release entry: ' + path.name)
        artifacts[path.name] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    report = {'complete': True, 'scope': 'H13/G1 command-line foundation for local owner testing',
              'source_commit': revision, 'G1': 'passed', 'G2': 'pending',
              'phase_2_owner_approval': 'pending', 'physical_hardware': 'pending',
              'public_binary_release': False, 'component_count': 134, 'source_input_count': 142,
              'dashboard': 'https://markaraujo.github.io/toddy-os/', 'artifacts': artifacts,
              'known_limitations': 'docs/FOUNDATION-TESTING.md in the source bundle',
              'build_instructions': 'docs/FRESH-BUILD.md in the source bundle',
              'recovery_instructions': 'docs/RECOVERY.md in the source bundle',
              'acceptance': 'docs/evidence/H13.md in the source bundle'}
    publication = ROOT / '.local/logs/h13-publication.json'
    if publication.exists():
        record = json.loads(publication.read_text())
        if record.get('commit') == revision and record.get('complete') is True:
            report['publication'] = record
    (directory / 'release-summary.json').write_text(json.dumps(report, indent=2) + '\n')
    checks = {name: row['sha256'] for name, row in artifacts.items()}
    checks['release-summary.json'] = digest(directory / 'release-summary.json')
    (directory / 'SHA256SUMS').write_text(''.join(sha + '  ' + name + '\n' for name, sha in sorted(checks.items())))
    subprocess.run(['sha256sum', '-c', 'SHA256SUMS'], cwd=directory, check=True)
    print(json.dumps({'complete': True, 'source_commit': revision, 'files_verified': len(checks),
                      'directory': str(directory.relative_to(ROOT))}))

if __name__ == '__main__':
    main()
