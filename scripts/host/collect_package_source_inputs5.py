#!/usr/bin/env python3
"""Fixed export5 native-record/catalog custody through the audited collector2."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect_package_source_inputs2 as original


def configure():
    source, destination = original.transfer.fixed_paths(5)
    old = '/mnt/lfs/sources/stage/toddy-package-export-2'
    if original.REMOTE.count(old) != 1:
        raise ValueError('Expected single fixed audited source-record root')
    original.transfer.DESTINATION = destination
    original.DESTINATION = destination / 'source-inputs'
    original.REMOTE = original.REMOTE.replace(old, source)


if __name__ == '__main__':
    if sys.argv[1:]:
        raise SystemExit('Fixed export5 source inputs only; no arbitrary paths')
    configure()
    original.run()
