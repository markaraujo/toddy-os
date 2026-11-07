#!/usr/bin/env python3
"""Retain raw image key findings and qualify only exact reviewed manual examples.

Passing this narrow check is not whole-image credential or release acceptance.
See ADR-0071 for the source/parser evidence and the remaining credential gates.
"""
import argparse
import base64
import binascii
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_private_key_material import MARKER, scan
from locked_inputs import locked_source
from package_backend import PackageBackend
import review_magic_database

SOURCE = 'openssl-4.0.3.tar.gz'
SOURCE_SHA = '325b5c806167c13b40b1ffeadfe0248197c00eccc4cf123ec1e28d2d2fd216d9'
PREFIX = '/usr/share/doc/openssl-4.0.3/'
REVIEWED = {
    'man3/PEM_read.pod': '46c0c181b8882eae8ea608f10c2a2e0e93897101354aabb8d4077fb9b62a498e',
    'html/man3/PEM_read.html': '38c3521bfaaa1e696c7da0b09cc1187163f881adacaf10d5b62571afae8162ce',
    'man3/PEM_read_bio_PrivateKey.pod': 'fe20186815d6246d255554a66b3181a054270515100b29d2c34894d9ef108c35',
    'html/man3/PEM_read_bio_PrivateKey.html': '8f02fadb2367ff02ecf71359cf68adf79669bede4a65bc6798236408b67a07cb',
    'man7/openssl-glossary.pod': '8437c819231db56ff64d831be97e9f717e0c1e84c46357ae8d6d6d377dfe7445',
    'html/man7/openssl-glossary.html': 'fcdb517c06a858cdcf0d481b8648337358745aae2c5ed5a29b80f409c5aa7017',
}
EXAMPLE = re.compile(r'-----BEGIN (?P<label>(?:RSA |DSA |EC |ENCRYPTED )?PRIVATE KEY)-----'
                     r'(?P<body>.*?)-----END (?P=label)-----', re.S)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def example(text):
    matches = list(EXAMPLE.finditer(text))
    if len(matches) != 1 or len(MARKER.findall(text.encode())) != 1:
        raise ValueError('Manual private-key markers differ from the reviewed example')
    body = ''.join(line.strip() for line in matches[0]['body'].splitlines()
                   if line.strip() and not line.strip().startswith(('Proc-Type:', 'DEK-Info:')))
    if '...' not in body:
        raise ValueError('Manual example lacks its reviewed placeholder')
    try:
        base64.b64decode(body, validate=True)
    except binascii.Error:
        pass
    else:
        raise ValueError('Manual example contains decodable key-shaped data')
    return '\n'.join(line.strip() for line in matches[0].group(0).strip().splitlines()) + '\n'


def review(backend, image, repository=Path('/opt/toddy-build'),
           records=Path('/var/log/toddy/packages'), cache=Path('/var/cache/toddy/packages')):
    image, root = Path(image), backend.target
    if (not backend.native or image.resolve() != image or not image.is_dir()
            or not any(image != root / area and image.is_relative_to(root / area)
                       for area in ('tmp', 'sources/stage'))):
        raise ValueError('Key-marker review requires a fresh private native image')
    raw = scan(image)
    qualified, unresolved, databases = [], [], []
    candidates = []
    for finding in raw['findings']:
        suffix = finding['path'].removeprefix(PREFIX)
        if finding['path'] == PREFIX + suffix and REVIEWED.get(suffix) == finding['sha256']:
            candidates.append((finding, suffix))
        elif finding['path'] == review_magic_database.PATH and finding['sha256'] == review_magic_database.SHA:
            databases.append(review_magic_database.prove(backend, image, repository, records, cache))
        else:
            unresolved.append(finding)
    provenance = None
    if candidates:
        database = image / 'var/lib/dpkg'
        if database.resolve() != database:
            raise ValueError('Image package database redirects')
        status_sha = digest(database / 'status')
        version, architecture, state = backend.run('dpkg-query',
            '--admindir=/' + str(database.relative_to(root)), '-W',
            '-f=${Version}\t${Architecture}\t${Status}', 'openssl',
            capture_output=True, text=True).stdout.split('\t')
        if (state != 'install ok installed' or architecture != 'amd64'
                or not re.fullmatch(r'4\.0\.3-[0-9A-Za-z.+~]+', version)):
            raise ValueError('Image OpenSSL package identity is not the reviewed version')
        record_path = records / f'openssl_{version}_{architecture}.json'
        package = cache / f'openssl_{version}_{architecture}.deb'
        if record_path.resolve() != record_path or package.resolve() != package:
            raise ValueError('OpenSSL package provenance redirects')
        record_sha = digest(record_path)
        record = json.loads(record_path.read_text())
        source = root / 'sources' / SOURCE
        frozen = locked_source(repository, SOURCE)
        if (record.get('installed') is not True or record['name'] != 'openssl'
                or record['version'] != version or digest(package) != record['archive_sha256']
                or not frozen or frozen['sha256'] != SOURCE_SHA
                or source.resolve() != source or digest(source) != SOURCE_SHA
                or not any(row['filename'] == SOURCE and row['sha256'] == SOURCE_SHA
                           for row in record['sources'])):
            raise ValueError('OpenSSL own-package or frozen-source provenance differs')
        # Use the already accepted native parser, not an unverified image executable.
        native = root / 'usr/bin/openssl'
        if native.resolve() != native or digest(native) != record['payload']['/usr/bin/openssl']['sha256']:
            raise ValueError('Accepted native parser differs from the own-package record')
        with tarfile.open(source) as archive:
            for finding, suffix in candidates:
                path = image / finding['path'][1:]
                info, entry = path.lstat(), record['payload'].get(finding['path'], {})
                if (path.resolve() != path or not stat.S_ISREG(info.st_mode)
                        or (info.st_mode, info.st_uid, info.st_gid) !=
                           (entry.get('mode'), entry.get('uid'), entry.get('gid'))
                        or digest(path) != finding['sha256'] or entry.get('sha256') != finding['sha256']):
                    raise ValueError('Reviewed image manual differs from own-package payload')
                pod = suffix.removeprefix('html/').removesuffix('.html').removesuffix('.pod') + '.pod'
                source_name = 'openssl-4.0.3/doc/' + pod
                original = archive.extractfile(source_name).read()
                if hashlib.sha256(original).hexdigest() != REVIEWED[pod]:
                    raise ValueError('Frozen manual source differs from the reviewed document')
                content = path.read_text()
                if suffix.endswith('.html'):
                    parser = HTMLText()
                    parser.feed(content)
                    content = ''.join(parser.parts)
                elif path.read_bytes() != original:
                    raise ValueError('Image POD differs from frozen source')
                rendered, source_example = example(content), example(original.decode())
                if rendered != source_example:
                    raise ValueError('Image manual example differs from frozen source')
                try:
                    backend.run('openssl', 'pkey', '-noout', '-check', '-passin', 'pass:',
                                input=rendered.encode(), capture_output=True, timeout=10)
                except subprocess.CalledProcessError as error:
                    if error.returncode != 1 or error.stdout:
                        raise ValueError('Native parser did not reject the manual as expected') from None
                    parser_stderr_sha = hashlib.sha256(error.stderr).hexdigest()
                else:
                    raise ValueError('Native parser accepted purported placeholder key data')
                qualified.append(dict(finding, classification='Exact frozen manual placeholder; not key material',
                    frozen_source_document=source_name, source_document_sha256=REVIEWED[pod],
                    normalized_example_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
                    native_parser_exit=1, native_parser_stderr_sha256=parser_stderr_sha))
        if digest(record_path) != record_sha or digest(database / 'status') != status_sha:
            raise ValueError('Package metadata changed during marker review')
        provenance = {'source_archive_sha256': SOURCE_SHA, 'package_record_sha256': record_sha,
                      'package_archive_sha256': record['archive_sha256'], 'image_status_sha256': status_sha}
    return {'raw_scan': raw, 'qualified_document_examples': qualified, 'unresolved_findings': unresolved,
            'provenance': provenance, 'qualified_format_databases': databases, 'private_key_marker_check_passed': not unresolved and not raw['special_nodes_not_read'],
            'whole_image_credential_audit_accepted': False, 'image_or_boot_accepted': False,
            'raw_findings_suppressed': False}


def main():
    subprocess.run(['python3', str(Path(__file__).with_name('require_gate.py'))], check=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    if not args.image.is_relative_to(Path('/mnt/lfs/sources/stage')):
        raise ValueError('Select a designated release staging tree')
    result = review(PackageBackend(), args.image)
    print(json.dumps(result, indent=2))
    if not result['private_key_marker_check_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
