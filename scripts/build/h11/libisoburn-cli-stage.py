#!/usr/bin/env python3
"""Stage the foundation CLI profile without the optional Tk frontend."""
import os
from pathlib import Path
import sys

stage = Path(sys.argv[1])
parent = Path('/mnt/lfs/sources/stage')
if (os.geteuid() or stage.resolve() != stage or not stage.is_dir()
        or stage == parent or not stage.is_relative_to(parent)):
    raise SystemExit('Require a physical native package stage')
paths = ['usr/bin/xorriso-tcltk', 'usr/share/man/man1/xorriso-tcltk.1',
         'usr/share/info/xorriso-tcltk.info']
for name in paths:
    path = stage / name
    if path.parent.resolve() != path.parent or not path.is_file() or path.is_symlink():
        raise SystemExit('Expected exact optional frontend input: ' + name)
profile = stage / 'usr/share/doc/libisoburn/profile.txt'
if profile.parent.resolve() != profile.parent or profile.is_symlink():
    raise SystemExit('Preserve redirected package profile')
for name in paths:
    (stage / name).unlink()
profile.write_text('''Native shared libburn/libisofs stack; no bundled replacement libraries.
CLI image construction and extraction are the selected foundation path.
The optional xorriso-tcltk command/manuals are omitted: Tk/wish is not installed.
The complete frontend sources remain in the frozen corresponding source archive.
Jigdo/libjte and libcdio support are disabled. No physical-media test is claimed.
Embedded MD5 detects accidental corruption; artifact identity uses SHA-256.
Toddy ADR-0077 probes Glibc sys/xattr.h and restores symlink ownership/times
without following link destinations; the source patch is retained here.
ADR-0098 records this CLI-only package revision; upstream remains 1.5.8.pl02.
''')
profile.chmod(0o644)
