#!/usr/bin/env python3
"""Require complete raw libc results; only the frozen-book failure is expected."""
from collections import Counter
import json
from pathlib import Path
import re


def classify(lines, exit_code):
    results=[]
    for line in lines:
        match=re.fullmatch(r'(PASS|FAIL|XFAIL|XPASS|UNSUPPORTED):\s+(.+)',line.strip())
        if match: results.append(match.groups())
    counts=Counter(status for status,name in results)
    expected={'io/tst-lchmod':'Frozen LFS 13.1-systemd 8.5 documents this failure in the LFS chroot.'}
    unexplained=[name for status,name in results
                 if status=='XPASS' or (status=='FAIL' and name not in expected)]
    failures={name:expected[name] for status,name in results if status=='FAIL' and name in expected}
    complete=len(results)>=6000 and counts['PASS']>0
    accepted=complete and not unexplained and exit_code in (0,2)
    if exit_code!=0 and not failures:
        accepted=False
    return {'suite_exit':exit_code,'counts':dict(counts),'complete':complete,
        'expected_failures':failures,'unexplained_failures':unexplained,
        'source':'LFS 13.1-systemd section 8.5','accepted':accepted}


def main():
    folder=Path('/mnt/lfs/sources/evidence/h07-glibc')
    exit_code=int((folder/'make-check.exit').read_text().strip())
    record=classify((folder/'tests-original.sum').read_text().splitlines(),exit_code)
    (folder/'classification.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))
    if not record['accepted']:
        raise SystemExit('Critical libc suite not accepted; diagnose raw evidence before installation')


if __name__=='__main__':
    main()
