#!/usr/bin/env python3
"""Classify the frozen Systemd suite; retain book-known namespace limitations."""
import collections
import json
from pathlib import Path
import sys


def evaluate(rows, raw_exit):
    if len(rows)!=1862 or len({r['name'] for r in rows})!=1862:
        raise ValueError('Incomplete/duplicate Systemd suite')
    counts=collections.Counter(r['result'] for r in rows)
    if set(counts)-{'OK','SKIP','FAIL'}:
        raise ValueError('Unexpected Systemd outcome')
    failed=[r for r in rows if r['result']=='FAIL']
    if not failed:
        if raw_exit!=0:raise ValueError('Nonzero suite without classified failure')
    else:
        if raw_exit!=1 or len(failed)!=1:
            raise ValueError('Unknown Systemd failures')
        row=failed[0]
        if row['name']!='core - systemd:test-namespace' or row['returncode']!=-6:
            raise ValueError('Unknown Systemd failure identity')
        stderr=row.get('stderr','')
        if ('/* test_process_is_owned_by_uid */' not in stderr or
            'src/test/test-namespace.c:391: Assertion failed: Expected "r" to succeed, but got error: -1/EPERM' not in stderr):
            raise ValueError('Unknown namespace failure cause')
    return {'groups':len(rows),'counts':dict(counts),'raw_ninja_exit':raw_exit,
            'known_chroot_failures':[r['name'] for r in failed],
            'all_pass':not failed,'native_namespace_retest_required_before_G1':bool(failed)}

if __name__=='__main__':
    base=Path(sys.argv[1]);rows=[json.loads(l) for l in Path(sys.argv[2]).read_text().splitlines()]
    result=evaluate(rows,int((base/'check.exit').read_text()))
    (base/'classification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
