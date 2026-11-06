"""Retain exact named/collected legal notices from authenticated source archives."""
import hashlib
import io
import zipfile
import json
from pathlib import Path,PurePosixPath
import re
import tarfile
from locked_inputs import locked_source


def is_notice(name):
    named=bool(re.match(r'^(COPYINGv?[0-9]*|COPYRIGHTS?|LICEN[CS](?:ES?|ING)|NOTICE|AUTHORS?|ARTISTIC)([._-]|$)',name.name,re.I))
    named=named or bool(re.match(r'^(README|ABOUT)[._-](LICEN[CS](?:ES?|ING)|COPYRIGHT)',name.name,re.I))
    collection=any(p.lower()=='licenses' for p in name.parts[:-1])
    # Packaging's licenses Python module is code, not a legal-text collection.
    code=name.suffix.lower() in {'.py','.c','.h','.cc','.cpp','.js','.ts','.rs'}
    return named or (collection and not code)


def embedded_zip_notices(data,member_name):
    results=[]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            name=PurePosixPath(member.filename)
            if member.is_dir() or not is_notice(name):continue
            if name.is_absolute() or '..' in name.parts or any(c in member.filename for c in '\r\n\t'):
                raise ValueError('Unsafe embedded legal notice path')
            if member.file_size>4*1024*1024:raise ValueError('Oversized embedded legal notice')
            payload=archive.read(member)
            results.append(({'path':member_name+'!'+member.filename,
                             'embedded_archive_sha256':hashlib.sha256(data).hexdigest(),
                             'sha256':hashlib.sha256(payload).hexdigest(),'size':len(payload)},payload))
    return results


def leading_c_notice(data):
    position=0;parts=[]
    while True:
        match=re.match(rb'\s*',data[position:]);position+=match.end()
        if data.startswith(b'/*',position):
            end=data.find(b'*/',position+2)
            if end<0:raise ValueError('Unterminated source license comment')
            parts.append(data[position:end+2]);position=end+2
        elif data.startswith(b'//',position):
            end=data.find(b'\n',position)
            if end<0:end=len(data)
            parts.append(data[position:end]);position=end
        else:break
    notice=b'\n'.join(parts)
    if re.search(rb'copyright|license|public domain|redistribution',notice,re.I):return notice
    return None


def selected_header_notices(archive,filename,policies):
    policy=policies.get(filename)
    if not policy:return []
    results=[]
    for member in archive.getmembers():
        if not member.isfile():continue
        name=PurePosixPath(member.name)
        if name.is_absolute() or '..' in name.parts:raise ValueError('Unsafe source header path')
        relative='/'.join(name.parts[1:])
        selected=relative in policy.get('paths',[])
        selected=selected or (any(relative.startswith(p) for p in policy.get('prefixes',[])) and name.suffix in policy.get('suffixes',[]))
        if not selected:continue
        data=archive.extractfile(member).read();notice=leading_c_notice(data)
        if notice:
            results.append(({'path':member.name+' [leading license comments]',
                             'source_file_sha256':hashlib.sha256(data).hexdigest(),
                             'sha256':hashlib.sha256(notice).hexdigest(),'size':len(notice)},notice))
    return results


def retain_source_notices(root,target,stage,package,filenames):
    destination=stage/'usr/share/doc'/package/'source-notices'
    if destination.exists():
        # Metadata upgrades regenerate from original source, not stale stage data.
        import shutil
        if destination.is_symlink():raise ValueError('Notice output must not be a symlink')
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    inventory=[]
    rows=json.loads((root/'config/component-licenses.json').read_text())['components']
    policies={}
    for component in rows:
        if component['name']==package:policies.update(component.get('extra_license_headers',{}))
    for filename in filenames:
        row=locked_source(root,filename)
        if not row:raise ValueError('Unknown notice source')
        source=target/'sources'/filename
        with source.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if sha!=row['sha256']:raise ValueError('Notice source integrity mismatch')
        result={'filename':filename,'source_sha256':sha,'url':row['url'],'notices':[]}
        if tarfile.is_tarfile(source):
            with tarfile.open(source) as archive:
                for header,payload in selected_header_notices(archive,filename,policies):
                    (destination/header['sha256']).write_bytes(payload)
                    result['notices'].append(header)
                for member in archive:
                    name=PurePosixPath(member.name)
                    if member.isfile() and member.name.endswith('.whl'):
                        if name.is_absolute() or '..' in name.parts:raise ValueError('Unsafe embedded source archive path')
                        if member.size>32*1024*1024:raise ValueError('Oversized embedded wheel for notice scan')
                        data=archive.extractfile(member).read()
                        for nested,payload in embedded_zip_notices(data,member.name):
                            (destination/nested['sha256']).write_bytes(payload)
                            result['notices'].append(nested)
                    if not member.isfile() or not is_notice(name):continue
                    if name.is_absolute() or '..' in name.parts or any(c in member.name for c in '\r\n\t'):
                        raise ValueError('Unsafe legal notice source path')
                    data=archive.extractfile(member).read()
                    digest=hashlib.sha256(data).hexdigest()
                    (destination/digest).write_bytes(data)
                    result['notices'].append({'path':member.name,'sha256':digest,'size':len(data)})
        inventory.append(result)
    (destination/'index.json').write_text(json.dumps({'sources':inventory,'scope':'Exact named legal notices and LICENSES directories; corresponding source per-file conditions also apply'},indent=2)+'\n')
