"""Retain exact named/collected legal notices from authenticated source archives."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import tarfile
from locked_inputs import locked_source


def is_notice(name):
    return bool(re.match(r'^(COPYING[0-9]*|COPYRIGHT|LICEN[CS]E|NOTICE|AUTHORS)([._-]|$)',name.name,re.I)) or any(p.lower()=='licenses' for p in name.parts[:-1])


def retain_source_notices(root,target,stage,package,filenames):
    destination=stage/'usr/share/doc'/package/'source-notices'
    if destination.exists():
        # Metadata upgrades regenerate from original source, not stale stage data.
        import shutil
        if destination.is_symlink():raise ValueError('Notice output must not be a symlink')
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    inventory=[]
    for filename in filenames:
        row=locked_source(root,filename)
        if not row:raise ValueError('Unknown notice source')
        source=target/'sources'/filename
        with source.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if sha!=row['sha256']:raise ValueError('Notice source integrity mismatch')
        result={'filename':filename,'source_sha256':sha,'url':row['url'],'notices':[]}
        if tarfile.is_tarfile(source):
            with tarfile.open(source) as archive:
                for member in archive:
                    name=PurePosixPath(member.name)
                    if not member.isfile() or not is_notice(name):continue
                    if name.is_absolute() or '..' in name.parts or any(c in member.name for c in '\r\n\t'):
                        raise ValueError('Unsafe legal notice source path')
                    data=archive.extractfile(member).read()
                    digest=hashlib.sha256(data).hexdigest()
                    (destination/digest).write_bytes(data)
                    result['notices'].append({'path':member.name,'sha256':digest,'size':len(data)})
        inventory.append(result)
    (destination/'index.json').write_text(json.dumps({'sources':inventory,'scope':'Exact named legal notices and LICENSES directories; corresponding source per-file conditions also apply'},indent=2)+'\n')
