#!/usr/bin/env python3
"""Extract and run the LFS 13.1 host check in the dedicated guest."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
URL = 'https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter02/hostreqs.html'
EXPECTED = '7d92798c0d4650521f16b86c2858df51b891ff9fe1ca044edf305d8c4767f10c'


class Extract(HTMLParser):
    active = False
    result = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'code' and ('class', 'literal') in attrs:
            self.active = True

    def handle_endtag(self, tag):
        if tag == 'code':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.result += data


def main():
    folder = ROOT / '.local/books'
    folder.mkdir(parents=True, exist_ok=True)
    page = folder / 'hostreqs.html'
    if not page.exists():
        subprocess.run(['curl', '-fLsS', URL, '-o', str(page)], check=True)
    if hashlib.sha256(page.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit('Host-check page changed; review it before executing')
    parser = Extract()
    parser.feed(page.read_text())
    script = parser.result[parser.result.index('#!/bin/bash'):] + '\n'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/host/vm.py'),
        'ssh', 'cd /tmp && bash -s'], input=script, text=True, capture_output=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    # The upstream script can print ERROR while returning zero. Check both.
    if result.returncode or 'ERROR:' in result.stdout or 'FATAL:' in result.stdout:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
