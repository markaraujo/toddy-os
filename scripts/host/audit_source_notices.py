#!/usr/bin/env python3
"""Inventory exact legal notices in frozen source archives, without execution."""
import concurrent.futures
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import tarfile

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'.local/legal/source-notices'
DEST.mkdir(parents=True,exist_ok=True)
locks=[('sources.lock.json','packages'),('security-overlay.lock.json','components'),('supplemental-sources.lock.json','components')]
rows={}
for filename,key in locks:
    for row in json.loads((ROOT/'config'/filename).read_text())[key]:rows[row['filename']]=row

def audit(row):
    source=ROOT/'.local/sources'/row['filename']
    with source.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=row['sha256']:raise ValueError('Frozen archive mismatch: '+source.name)
    result={'filename':source.name,'source_sha256':actual,'url':row['url'],'notices':[]}
    if not tarfile.is_tarfile(source):
        result['archive_type']='not_tar';return result
    destination=DEST/actual
    destination.mkdir(exist_ok=True)
    with tarfile.open(source) as archive:
        for member in archive:
            name=PurePosixPath(member.name)
            if not member.isfile():continue
            named=bool(re.match(r'^(COPYING[0-9]*|COPYRIGHT|LICEN[CS]E|NOTICE|AUTHORS)([._-]|$)',name.name,re.I))
            legal_directory=any(part.lower()=='licenses' for part in name.parts[:-1])
            if not (named or legal_directory):continue
            if name.is_absolute() or '..' in name.parts or any(c in member.name for c in '\r\n\t'):
                raise ValueError('Unsafe notice member')
            data=archive.extractfile(member).read()
            content_sha=hashlib.sha256(data).hexdigest()
            (destination/content_sha).write_bytes(data)
            result['notices'].append({'path':member.name,'sha256':content_sha,'size':len(data)})
    result['scope']='Exact named legal notices; embedded per-file licenses and bundled component expressions require separate review'
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:results=list(executor.map(audit,rows.values()))
(DEST/'inventory.json').write_text(json.dumps({'complete_license_review':False,'sources':sorted(results,key=lambda r:r['filename'])},indent=2)+'\n')
print(json.dumps({'archives':len(results),'notices':sum(len(r['notices']) for r in results),'inventory_sha256':hashlib.sha256((DEST/'inventory.json').read_bytes()).hexdigest(),'destination':str(DEST.relative_to(ROOT))}))
