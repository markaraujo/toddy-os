"""Prove an exact key-marker hit is File's source-built format database."""
import hashlib
import json
from pathlib import Path
import re
import stat
import tarfile
import tempfile

from locked_inputs import locked_source

PATH = '/usr/share/misc/magic.mgc'
SHA = 'c2f4e7e55b0ee33c181ada80b065f9f8a58633c9806e8bd3353253c68324f268'
SOURCE = 'file-5.48.tar.gz'
SOURCE_SHA = 'ed14656883b23a364b4057c05595d93252da9bc473d30106519519d0da141283'
MAKEFILE_SHA = '4871c42e2fa589837f80b333aff9376dca6ef6558a6ae70b50833d744d769dde'
SSH_RULE_SHA = '38e6e7049f18a557950a50167c40a4dff7529bbfdaaa240d612889431cd382fd'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prove(backend, image, repository, records, cache):
    root, image = backend.target, Path(image)
    record_path = records / 'file_5.48-1+toddy1_amd64.json'
    record = json.loads(record_path.read_text())
    frozen = locked_source(repository, SOURCE)
    source = root / 'sources' / SOURCE
    package = cache / 'file_5.48-1+toddy1_amd64.deb'
    if (record.get('installed') is not True or record['name'] != 'file'
            or record['version'] != '5.48-1+toddy1' or not frozen
            or frozen['sha256'] != SOURCE_SHA or digest(source) != SOURCE_SHA
            or digest(package) != record['archive_sha256']
            or not any(row['filename'] == SOURCE and row['sha256'] == SOURCE_SHA for row in record['sources'])):
        raise ValueError('Magic database source/package provenance differs')
    state = backend.run('dpkg-query', '--admindir=/' + str((image / 'var/lib/dpkg').relative_to(root)),
        '-W', '-f=${Version}\t${Status}', 'file', capture_output=True, text=True).stdout
    if state != '5.48-1+toddy1\tinstall ok installed':
        raise ValueError('Image File package identity differs')
    def own(path, virtual):
        row = record['payload'][virtual]
        info = path.lstat()
        if (path.resolve() != path or not stat.S_ISREG(info.st_mode)
                or (info.st_mode, info.st_uid, info.st_gid) != (row['mode'], row['uid'], row['gid'])
                or digest(path) != row['sha256']):
            raise ValueError('Magic database/compiler own payload differs')
    own(image / PATH[1:], PATH)
    if digest(image / PATH[1:]) != SHA:
        raise ValueError('Unreviewed magic database generation')
    # Validate the compiler and its complete own regular payload, including libmagic.
    for virtual, row in record['payload'].items():
        if row.get('sha256'):
            own(root / virtual[1:], virtual)
    work = Path(tempfile.mkdtemp(prefix='h11-magic-source-', dir=root / 'sources/stage'))
    rules = work / 'magic'; rules.mkdir(mode=0o700)
    with tarfile.open(source) as archive:
        makefile = archive.extractfile('file-5.48/magic/Makefile.am').read()
        if hashlib.sha256(makefile).hexdigest() != MAKEFILE_SHA:
            raise ValueError('Frozen File recipe differs')
        section = makefile.decode().split('MAGIC_FRAGMENTS =', 1)[1].split('EXTRA_DIST =', 1)[0]
        names = re.findall(r'\$\((MAGIC_DIR|MAGIC_FRAGMENT_DIR)\)/([A-Za-z0-9_.+-]+)', section)
        if len(names) != 358 or len({name for _, name in names}) != 358:
            raise ValueError('Frozen magic-fragment set differs')
        hashes = {}
        for variable, name in names:
            member = 'file-5.48/magic/' + ('Magdir/' if variable == 'MAGIC_FRAGMENT_DIR' else '') + name
            if not archive.getmember(member).isfile():
                raise ValueError('Magic fragment is not regular source data')
            data = archive.extractfile(member).read()
            (rules / name).write_bytes(data)
            hashes[member] = hashlib.sha256(data).hexdigest()
        if hashes['file-5.48/magic/Magdir/ssh'] != SSH_RULE_SHA:
            raise ValueError('Reviewed key-format recognition rules differ')
    command = ['bash', '-c', 'cd -- "$1" && exec /usr/bin/file -C -m magic',
               'magic-compile', '/' + str(work.relative_to(root))]
    with (work / 'compile.log').open('x') as log:
        backend.run(*command, stdout=log, stderr=-2, timeout=60)
    regenerated = work / 'magic.mgc'
    if digest(regenerated) != SHA or digest(source) != SOURCE_SHA:
        raise ValueError('Source-regenerated magic database differs from reviewed image')
    result = {'path': PATH, 'sha256': SHA, 'classification': 'Exact source-regenerated format-recognition database; markers are recognition rules',
              'source_archive_sha256': SOURCE_SHA, 'makefile_sha256': MAKEFILE_SHA,
              'ssh_rule_sha256': SSH_RULE_SHA, 'source_fragments': hashes,
              'native_compile_exit': 0, 'regenerated_sha256': SHA,
              'compile_log_sha256': digest(work / 'compile.log'), 'workspace': str(work),
              'package_record_sha256': digest(record_path), 'package_archive_sha256': record['archive_sha256']}
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
