"""Read-only frozen dosfstools stage/upstream-result checks; no filesystem tools."""
import argparse
import json
from pathlib import Path
import re

ALIASES={'dosfslabel':'fatlabel','dosfsck':'fsck.fat','fsck.msdos':'fsck.fat','fsck.vfat':'fsck.fat','mkdosfs':'mkfs.fat','mkfs.msdos':'mkfs.fat','mkfs.vfat':'mkfs.fat'}


def tests(directory,makefile):
    source=makefile.read_text();block=source.split('TESTS = ',1)[1].split('\n\n',1)[0];names=block.replace('\\\n',' ').split()
    if len(names)!=40 or len(set(names))!=40 or source.split('XFAIL_TESTS = ',1)[1].splitlines()[0]!='check-huge.fsck':raise ValueError('Frozen upstream test inventory changed')
    expected={Path(name).stem+'.trs':name for name in names};actual={p.name for p in directory.glob('*.trs')}
    if set(expected)!=actual:raise ValueError('All40 upstream results required')
    rows=[]
    for name,test in sorted(expected.items()):
        result=re.findall(r'^:test-result:\s*(\S+)\s*$',(directory/name).read_text(),re.M)
        wanted='XFAIL' if test=='check-huge.fsck' else 'PASS'
        if result!=[wanted]:raise ValueError('Upstream failure/skip/unexpected result: '+test)
        rows.append({'test':test,'result':wanted})
    return {'total':40,'pass':39,'upstream_expected_fail':1,'skip':0,'fail':0,'error':0,'xpass':0,'results':rows}


def layout(stage):
    for name in ('mkfs.fat','fsck.fat','fatlabel'):
        path=stage/'usr/sbin'/name
        if not path.is_file() or path.is_symlink() or path.read_bytes()[:4]!=b'\x7fELF':raise ValueError('Required native sbin ELF missing')
    for name,target in ALIASES.items():
        path=stage/'usr/sbin'/name
        if not path.is_symlink() or str(path.readlink())!=target:raise ValueError('Upstream compatibility link differs')
    for name in ('COPYING','README'):
        path=stage/'usr/share/doc/dosfstools-4.2'/name
        if not path.is_file() or path.is_symlink() or not path.stat().st_size:raise ValueError('Required upstream documentation missing')
    return {'programs':['/usr/sbin/'+name for name in ('mkfs.fat','fsck.fat','fatlabel')],'aliases':ALIASES}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['tests']);parser.add_argument('directory',type=Path);parser.add_argument('makefile',type=Path)
    args=parser.parse_args();print(json.dumps(tests(args.directory,args.makefile),sort_keys=True))
