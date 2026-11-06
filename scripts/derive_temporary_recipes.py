#!/usr/bin/env python3
"""Derive reviewable chapter-6 scripts from the SHA-pinned LFS HTML archive.

Generated scripts are reviewed and committed, never directly executed by this
extractor. Build execution remains gated by H04 and per-package postconditions.
"""
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / '.local/books/lfs/13.1'
OUT = ROOT / 'scripts/build/h05'


class Commands(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.commands = []
        self.current = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'pre' and ('class', 'userinput') in attrs:
            self.active = True
            self.current = ''

    def handle_endtag(self, tag):
        if tag == 'pre' and self.active:
            self.commands.append(self.current)
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.current += data


# Exact source tree and archive names from the frozen chapter and source lock.
PACKAGES = [
    ('m4', 'm4-1.4.21', '.tar.xz'), ('ncurses', 'ncurses-6.6', '.tar.gz'),
    ('bash', 'bash-5.3', '.tar.gz'), ('coreutils', 'coreutils-9.11', '.tar.xz'),
    ('diffutils', 'diffutils-3.12', '.tar.xz'), ('file', 'file-5.48', '.tar.gz'),
    ('findutils', 'findutils-4.11.0', '.tar.xz'), ('gawk', 'gawk-5.4.1', '.tar.xz'),
    ('grep', 'grep-3.12', '.tar.xz'), ('gzip', 'gzip-1.14', '.tar.xz'),
    ('make', 'make-4.4.1', '.tar.gz'), ('patch', 'patch-2.8', '.tar.xz'),
    ('sed', 'sed-4.10', '.tar.xz'), ('tar', 'tar-1.35', '.tar.xz'),
    ('xz', 'xz-5.8.3', '.tar.xz'), ('binutils-pass2', 'binutils-2.47', '.tar.xz'),
    ('gcc-pass2', 'gcc-16.2.0', '.tar.xz')]


def main():
    lock = json.loads((ROOT / 'config/books.lock.json').read_text())
    archive = ROOT / '.local/books/LFS-BOOK-13.1.tar.xz'
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == lock['lfs']['archive_sha256']
    source_names = {r['filename'] for r in json.loads((ROOT / 'config/sources.lock.json').read_text())['packages']}
    OUT.mkdir(exist_ok=True)
    for name, directory, extension in PACKAGES:
        filename = directory + extension
        assert filename in source_names, filename
        page = BOOK / 'chapter06' / (name + '.html')
        extractor = Commands()
        extractor.feed(page.read_text())
        assert extractor.commands
        commands = '\n\n'.join(extractor.commands)
        for dependency in ['mpfr-4.2.2.tar.xz', 'gmp-6.3.0.tar.xz', 'mpc-1.4.1.tar.xz']:
            commands = commands.replace('tar -xf ../' + dependency, 'unpack ' + dependency)
        prelude = ('#!/bin/bash\n# LFS 13.1-systemd chapter 6: ' + name + '\n'
                   '# Derived by scripts/derive_temporary_recipes.py; review before execution.\n'
                   'source /opt/toddy-build/scripts/build/h04/common.sh\n'
                   f'unpack {filename}\ncd {directory}\n')
        if name == 'm4':
            prelude += 'mkdir -p "$LFS/usr/share"\n'
        ending = (f'\nif [[ -f config.log ]]; then cp config.log "$LFS/sources/evidence/h05-{name}-config.log"; fi\n'
                  f'cd "$LFS/sources"\nrm -rf {directory}\n')
        output = OUT / (name + '.sh')
        output.write_text(prelude + commands + '\n' + ending)
        output.chmod(0o755)
        print(f'Derived {name}: {len(extractor.commands)} command blocks; HTML SHA-256 {hashlib.sha256(page.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
