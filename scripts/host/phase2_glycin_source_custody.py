#!/usr/bin/env python3
"""Retire newly expanded Glycin sources only after exact retained-archive proof."""
import hashlib
import json
import os
from pathlib import Path
import shutil

from phase2_retire_expanded_sources import archive_tree
from phase2_retire_source_copies import ROOT, sha, tree


def main():
    ledger = ROOT / '.local/phase2/glycin-source-custody.json'
    assert not ledger.exists(), 'Reconcile prior custody; no replay'
    context = ROOT / '.local/phase2/glycin-vendor-1'
    assert (context/'exit').read_text().strip() == '0'
    proof = json.loads((context/'verified.json').read_text())
    assert proof['host_source_compilations'] == 0
    parent, = proof['parents']
    assert parent['name'] == 'glycin' and len(parent['packages']) == 307
    rows = {r['name']: r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']}
    selected = []
    for name, path, root in [('glycin', context/'source/glycin-2.1.5', 'glycin-2.1.5'),
                             ('glycin-vendor', context/'glycin/vendor', 'vendor')]:
        row = rows[name]
        archive = ROOT / '.local/sources' / row['filename']
        assert sha(archive) == row['sha256']
        selected.append((path, archive, root, False))
    registry = ROOT / '.local/phase2/rust-vendor-1/home/registry'
    for index in sorted((registry/'src').iterdir()):
        assert index.is_dir() and not index.is_symlink() and index.name.startswith('index.crates.io-')
        for package in sorted(index.iterdir()):
            selected.append((package, registry/'cache'/index.name/(package.name+'.crate'), package.name, True))
    record = {'scope': 'New Glycin expanded source/vendor and re-expanded Cargo registry sources only; all compressed archives, locks, index, guest inputs, compiled packages and evidence retained',
              'state': 'verifying', 'sources': []}
    def save():
        part = ledger.with_suffix('.part')
        with part.open('x') as f:
            f.write(json.dumps(record, indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(ledger)
    save()
    for path, archive, root, cargo in selected:
        assert path.resolve() == path and path.is_dir() and not path.is_symlink()
        assert archive.is_file() and not archive.is_symlink()
        actual, expected = tree(path), archive_tree(archive, root)
        if cargo:
            assert (path/'.cargo-ok').read_bytes() == b'{"v":1}'
            assert actual.pop('.cargo-ok') == {'sha256': sha(path/'.cargo-ok'), 'bytes': 7}
        assert actual == expected, str(path)+' source drift; preserve everything'
        record['sources'].append({'path': str(path.relative_to(ROOT)), 'archive': str(archive.relative_to(ROOT)),
                                  'archive_sha256': sha(archive), 'entries': len(actual),
                                  'manifest_sha256': hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                                  'inode': path.stat().st_ino, 'cargo_marker_only': cargo, 'state': 'verified'})
    record['state'] = 'verified';save()
    record['available_before'] = shutil.disk_usage(ROOT).free
    for row in record['sources']:
        path = ROOT / row['path']
        assert path.resolve() == path and not path.is_symlink() and path.stat().st_ino == row['inode']
        assert sha(ROOT/row['archive']) == row['archive_sha256']
        row['state'] = 'retiring';save()
        shutil.rmtree(path);assert not path.exists()
        row['state'] = 'retired';save()
    record['available_after'] = shutil.disk_usage(ROOT).free
    record['reclaimed_bytes'] = record['available_after']-record['available_before']
    record['state'] = 'complete'
    record['recovery'] = 'Restore exact retained source/vendor archives only into absent paths when needed. Cargo re-extracts retained checked compressed cache; do not rerun custody.'
    save()
    print(json.dumps({k: record[k] for k in ['state','available_before','available_after','reclaimed_bytes']}))


if __name__ == '__main__':
    main()
