#!/usr/bin/env python3
"""Retain only the frozen book-known prezeroed allocation-count exception."""
import json
from pathlib import Path
import sys


def evaluate(output, failures, actual, expected, raw_exit):
    if raw_exit!=2 or failures!=['m_assume_storage_prezeroed.failed']:
        raise ValueError('Unknown E2fsprogs failure/exit')
    if '393 tests succeeded\t1 tests failed' not in output or 'Tests failed: m_assume_storage_prezeroed ' not in output:
        raise ValueError('Incomplete/changed E2fsprogs suite')
    if actual!='> 10000\n232\n' or expected!='> 10000\n224\n':
        raise ValueError('Unknown prezeroed allocation mismatch')
    return {'pass':393,'known_failures':['m_assume_storage_prezeroed'],
            'raw_make_exit':raw_exit,'all_pass':False,
            'expected_allocated_sectors':224,'actual_allocated_sectors':232,
            'installed_ext4_roundtrip_required':True}

if __name__=='__main__':
    evidence=Path(sys.argv[1]);tests=Path(sys.argv[2]);source=Path(sys.argv[3])
    result=evaluate((evidence/'check.log').read_text(),sorted(p.name for p in tests.glob('*.failed')),
                    (tests/'m_assume_storage_prezeroed.out').read_text(),
                    (source/'tests/m_assume_storage_prezeroed/expect').read_text(),
                    int((evidence/'check.exit').read_text()))
    (evidence/'classification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
