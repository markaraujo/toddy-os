"""Bind an initramfs to preserved assembly and native compression evidence.

The production caller owns milestone and build locks. Private component tests
can inspect their own generations; this grants no full-root or boot acceptance.
"""
import hashlib
import json
from pathlib import Path
import re
import stat

HERE = Path(__file__).resolve().parent


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def physical(root, path, *, directory=False):
    path = Path(path)
    if (path.resolve() != path or not any((directory or path != root / area) and path.is_relative_to(root / area)
            for area in ('tmp', 'sources/stage'))):
        raise ValueError('Initramfs input must be physical private target evidence')
    info = path.lstat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    parent = path.parent.stat()
    if (not kind(info.st_mode) or info.st_uid != 0 or info.st_gid != 0 or info.st_mode & 0o022
            or parent.st_uid != 0 or parent.st_gid != 0 or parent.st_mode & 0o022
            or info.st_dev != root.stat().st_dev):
        raise ValueError('Initramfs input is not protected same-filesystem state')
    return path


def verify(root, path, release, assembler=HERE / 'assemble_root.py'):
    root, path = Path(root), Path(path)
    if root.resolve() != root or not root.is_dir() or type(release) is not bool:
        raise ValueError('Canonical target and explicit assembly profile required')
    physical(root, path)
    report = json.loads(path.read_text())
    if (path.name != 'compression.json' or report.get('work') != str(path.parent)
            or report.get('complete') is not True or 'error' in report
            or any(report.get(key) is not True for key in (
                'source_unchanged', 'native_extraction_and_acl_restore_verified', 'sparse_allocation_preserved'))):
        raise ValueError('Native root compression/readback is incomplete')
    epoch = report.get('epoch')
    if type(epoch) is not int or not 0 <= epoch <= 0xffffffff:
        raise ValueError('Compression epoch is not representable in newc')
    binding = report.get('assembly_binding', {})
    if type(binding.get('release_profile')) is not bool or binding['release_profile'] != release:
        raise ValueError('Missing or mismatched production assembly binding')
    journal_path = physical(root, Path(binding['journal']))
    manifest_path = physical(root, Path(binding['manifest']))
    if digest(journal_path) != binding['journal_sha256'] or digest(manifest_path) != binding['manifest_sha256']:
        raise ValueError('Assembly evidence changed after compression')
    journal = json.loads(journal_path.read_text())
    if (journal.get('assembled') is not True or journal.get('release_profile') is not release
            or journal.get('evidence') != str(journal_path.parent)
            or journal.get('image') != report.get('image')
            or journal.get('assembler_sha256') != digest(assembler)):
        raise ValueError('Compression belongs to a different assembly generation/profile')
    actions = [row for row in journal['actions'] if row['step'] == 'image-manifest']
    if (len(actions) != 1 or not actions[0]['finished']
            or Path(actions[0]['report']).name != actions[0]['report']
            or journal_path.parent / actions[0]['report'] != manifest_path
            or actions[0]['sha256'] != binding['manifest_sha256']):
        raise ValueError('Compression does not bind the final assembly manifest')
    source = physical(root, path.parent / 'source-manifest.json')
    if json.loads(source.read_text()) != json.loads(manifest_path.read_text()):
        raise ValueError('Compressed source manifest differs from final assembly')
    steps = report.get('steps', [])
    if [row.get('name') for row in steps] != ['compress', 'extract', 'restore-acls']:
        raise ValueError('Native compression stages are incomplete or out of order')
    evidence = {str(path): digest(path), str(journal_path): digest(journal_path),
                str(manifest_path): digest(manifest_path), str(source): digest(source)}
    for step in steps:
        log = physical(root, path.parent / (step['name'] + '.log'))
        if type(step.get('exit')) is not int or step['exit'] != 0 or digest(log) != step['log_sha256']:
            raise ValueError('Native compression exit/log differs')
        evidence[str(log)] = digest(log)
    artifact = physical(root, path.parent / 'rootfs.squashfs')
    if (report.get('artifact') != str(artifact) or artifact.stat().st_size != report.get('artifact_bytes')
            or not re.fullmatch('[0-9a-f]{64}', report.get('artifact_sha256', ''))
            or digest(artifact) != report['artifact_sha256']):
        raise ValueError('Compressed artifact differs from verified native readback')
    evidence[str(artifact)] = report['artifact_sha256']
    return {'compression_bound': True, 'release_profile': release, 'epoch': epoch,
            'rootfs_sha256': report['artifact_sha256'], 'artifact': str(artifact),
            'source_image': report['image'], 'assembly_evidence_directory': str(journal_path.parent),
            'evidence_sha256': evidence, 'native_boot_verified': False}


def unchanged(root, binding):
    for name, sha in binding['evidence_sha256'].items():
        if digest(physical(Path(root), Path(name))) != sha:
            raise ValueError('Bound compression/assembly input changed during initramfs generation')
