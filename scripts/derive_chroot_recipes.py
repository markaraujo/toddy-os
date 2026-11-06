#!/usr/bin/env python3
"""Extract reviewed, pinned LFS chapter-7 commands for the native chroot.

This emits scripts for review, not execution. The separate H06 driver checks
H05 first and the guest wrapper verifies/extracts each archive outside chroot.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('derive_temp', ROOT / 'scripts/derive_temporary_recipes.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BOOK = ROOT / '.local/books/lfs/13.1'
OUT = ROOT / 'scripts/build/h06'


def commands(section):
    parser = module.Commands()
    parser.feed((BOOK / 'chapter07' / (section + '.html')).read_text())
    return '\n\n'.join(parser.commands)


def main():
    lock = json.loads((ROOT / 'config/books.lock.json').read_text())
    with (ROOT / '.local/books/LFS-BOOK-13.1.tar.xz').open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == lock['lfs']['archive_sha256']
    OUT.mkdir(exist_ok=True)
    bootstrap = commands('creatingdirs') + '\n' + commands('createfiles')
    # The book re-execs an interactive shell only to refresh the user prompt.
    # Each native recipe starts a new clean shell; do not replace this script.
    bootstrap = bootstrap.replace('exec /usr/bin/bash --login', ': # New clean shells are used for subsequent recipes.')
    (OUT / 'bootstrap-inner.sh').write_text('#!/bin/bash\nset -euo pipefail\n' + bootstrap + '\n')
    packages = [('gettext','gettext-1.0','.tar.xz'),('bison','bison-3.8.2','.tar.xz'),
        ('perl','perl-5.44.0','.tar.xz'),('zlib','zlib-1.3.2','.tar.gz'),
        ('mpdecimal','mpdecimal-4.0.1','.tar.gz'),('Python','Python-3.14.7','.tar.xz'),
        ('texinfo','texinfo-7.3','.tar.xz'),('util-linux','util-linux-2.42.2','.tar.xz')]
    known = {r['filename'] for r in json.loads((ROOT/'config/sources.lock.json').read_text())['packages']}
    for section, directory, extension in packages:
        name = section.lower()
        filename = directory + extension
        assert filename in known
        inner = f'#!/bin/bash\nset -euo pipefail\ncd /sources/{directory}\n' + commands(section)
        inner += f'\nif [[ -f config.log ]]; then cp config.log /sources/evidence/h06-{name}-config.log; fi\n'
        (OUT / f'{name}-inner.sh').write_text(inner)
        outer = f'''#!/bin/bash
# LFS 13.1-systemd chapter 7: {section}; guest-root wrapper.
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" {filename}
chroot_run < /opt/toddy-build/scripts/build/h06/{name}-inner.sh
rm -rf "$LFS/sources/{directory}"
'''
        (OUT / f'{name}.sh').write_text(outer)
    for path in OUT.glob('*.sh'):
        path.chmod(0o755)
    print('Derived native bootstrap and eight chapter-7 recipes; review before use.')


if __name__ == '__main__':
    main()
