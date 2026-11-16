#!/usr/bin/python3 -I
"""Unsigned curated acquisition declarations from parent-signed flat APT assets."""
import argparse
from email.utils import parsedate_to_datetime
import gzip
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(HERE)]
import offline_payload as p
import archive_metadata as metadata
from runtime.setup.releases import (DIRECTORY,RELEASE_PACKAGES,RELEASE_PERMISSIONS,POSTCONDITIONS,
    validate_declaration,signature)
from runtime.setup.runtime_compat import RUNTIME_PROFILE
from runtime.setup.pending import _encode

ORDER=('toddy-agent','toddy-executor','nodejs','llama-cpp')


def source_line(origin):
    if not isinstance(origin,str) or any(ord(c)<=32 or ord(c)>=127 for c in origin):raise ValueError('Explicit public repository origin required')
    uri=urlsplit(origin)
    if uri.username or uri.password or uri.query or uri.fragment or not (
        uri.scheme=='https' and uri.hostname or uri.scheme=='file' and not uri.netloc and uri.path==str(DIRECTORY/'repository')):
        raise ValueError('Credential-free HTTPS or fixed offline repository only')
    return ('deb [signed-by='+str(DIRECTORY/'archive-keyring.gpg')+'] '+origin+' ./\n').encode()


def verified_repository(directory,trust,*,now=None):
    """Verify actual public signatures; does not qualify APT or a package flow."""
    directory=Path(directory);receipt=p.strict(p.regular(directory/'archive-export.json').read_bytes())
    if receipt.get('version')!=1 or receipt.get('kind')!='unsigned-flat-native-archive-export' or receipt.get('public_fingerprint')!=trust['fingerprint'] or receipt.get('public_keyring_sha256')!=trust['keyring_sha256'] or receipt.get('producer_sha256')!=p.digest(metadata.__file__) or not isinstance(receipt.get('files'),dict):raise ValueError('Actual unsigned export and independent public pins required')
    metadata.valid_window(receipt['issued_unix'],receipt['expires_unix'],trust,now=now)
    original_signatures={name:p.digest(p.regular(directory/name)) for name in ('archive-export.json','Release.gpg','InRelease')}
    expected=set(receipt['files'])|{'archive-export.json','Release.gpg','InRelease'}
    if {path.name for path in directory.iterdir()}!=expected:raise ValueError('Only flat reviewed public assets and two parent signatures permitted')
    for name,digest in receipt['files'].items():
        if not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9_.+-]+',name) or p.digest(p.regular(directory/name))!=digest:raise ValueError('Flat exported asset changed')
    key=directory/'archive-keyring.gpg'
    if p.digest(key)!=trust['keyring_sha256'] or key.read_bytes()!=trust['bytes']:raise ValueError('Exported public key differs')
    for detached,path in ((directory/'Release.gpg',directory/'Release'),(None,directory/'InRelease')):
        if signature(key,detached,p.regular(path))!=trust['fingerprint']:raise ValueError('Actual signature primary differs from independent public pin')
    # A valid InRelease for a different Release is not the signed index reviewed.
    with tempfile.TemporaryDirectory(prefix='toddy-verified-release-') as temporary:
        clear=Path(temporary)/'Release'
        result=subprocess.run(['/usr/bin/gpgv','--keyring',str(key),'--output',str(clear),str(directory/'InRelease')],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            env={'PATH':'/usr/bin:/bin','HOME':temporary,'LC_ALL':'C'},timeout=10)
        if result.returncode or clear.read_bytes()!=(directory/'Release').read_bytes():raise ValueError('Clear-signed and detached Release differ')
    release=p.deb822((directory/'Release').read_text())
    if release.get('Origin')!='Toddy OS' or int(parsedate_to_datetime(release['Date']).timestamp())!=receipt['issued_unix'] or int(parsedate_to_datetime(release['Valid-Until']).timestamp())!=receipt['expires_unix']:raise ValueError('Signed finite release identity differs')
    packages=(directory/'Packages').read_bytes()
    if gzip.decompress((directory/'Packages.gz').read_bytes())!=packages:raise ValueError('Compressed Packages differs')
    hashes={row.split()[2]:(row.split()[0],int(row.split()[1])) for row in release['SHA256'].splitlines() if row.strip()}
    if hashes!={name:(p.digest(directory/name),(directory/name).stat().st_size) for name in ('Packages','Packages.gz')}:raise ValueError('Signed Packages index bindings differ')
    rows={}
    for paragraph in packages.decode().strip().split('\n\n'):
        row=p.deb822(paragraph);identity=row.get('Package')
        if identity in rows:raise ValueError('One exact package version per flat source required')
        rows[identity]=row
    declared={row['name']:row for row in receipt['packages']}
    if len(declared)!=len(receipt['packages']) or set(rows)!=set(declared):raise ValueError('Signed Packages and export package set differ')
    for name,row in declared.items():
        actual=rows[name]
        if (actual.get('Version'),actual.get('Architecture'),actual.get('Filename'),actual.get('SHA256'),actual.get('Size'))!=(row['version'],row['architecture'],row['asset'],row['archive_sha256'],str(row['archive_bytes'])):raise ValueError('Signed exact archive identity differs')
    if any(p.digest(p.regular(directory/name))!=digest for name,digest in {**receipt['files'],**original_signatures}.items()):raise ValueError('Signed export changed during verification')
    return receipt,rows


def terms(release_id,packages,origin=None):
    text=['Experimental Toddy native package review: '+release_id,
        'This declaration is not runtime qualification or authority. Installation requires a separately qualified signed catalog, explicit terms review and owner authorization.',
        'Package installation does not activate the agent/executor/local runtime, download a model, save a key, contact a provider or grant administration.',
        'Review the exact included copyright and source notices; mixed package-specific terms apply. No license acceptance is inferred from downloading this metadata.','']
    for row in packages:
        text.extend([row['name']+' '+row['version']+' '+row['architecture'],
            'Archive SHA-256: '+row['archive_sha256']+'; bytes: '+str(row['archive_bytes']),
            'Unpacked payload bytes: '+str(row['installed_bytes']),
            'Copyright: '+row['copyright']['path']+' SHA-256 '+row['copyright']['sha256']])
        for kind,asset in row['legal_assets'].items():
            text.append('Exact public legal asset: '+((origin.rstrip('/')+'/') if origin else '')+asset+' SHA-256 '+row[kind]['sha256'])
        notice=row.get('source_notices_index')
        if notice:text.append('Source notices: '+notice['path']+' SHA-256 '+notice['sha256'])
        for source in row['sources']:
            text.append('Public source: '+str(source.get('url',source.get('name','included source inventory')))+' SHA-256 '+source['sha256'])
        text.append('')
    data=('\n'.join(text)+'\n').encode()
    if not 0<len(data)<=65536:raise ValueError('Exact legal review exceeds supported bounded terms')
    return data


def release_declaration(release_id,packages,generation,origin=None):
    """Pure formatter/validator; callers supply separately verified exact rows."""
    if release_id not in RELEASE_PACKAGES or {row['name'] for row in packages}!=RELEASE_PACKAGES[release_id] or len(packages)!=len(RELEASE_PACKAGES[release_id]):raise ValueError('Exact curated declaration package set')
    legal=terms(release_id,packages,origin);legal_sha=hashlib.sha256(legal).hexdigest()
    row={'id':release_id,'artifact_id':'phase2-g'+str(generation)+'-'+release_id,
        'packages':[{'name':item['name'],'version':item['version'],'architecture':item['architecture'],
            'bytes':item['archive_bytes'],'installed_bytes':item['installed_bytes'],'sha256':item['archive_sha256']} for item in packages],
        'postconditions':{virtual:digest for item in packages for virtual,digest in item['postconditions'].items()},
        'terms_sha256':legal_sha,'license':'Mixed package-specific licenses; review the exact included copyright and source notices.',
        'permissions':RELEASE_PERMISSIONS[release_id],'requires_owner_authorization':True,'auto_activate':False}
    if any(item['name']=='llama-cpp' for item in packages):row['runtime_profile']=RUNTIME_PROFILE
    validate_declaration(row,directory=DIRECTORY,read=lambda path,**_options:legal if path==DIRECTORY/'terms'/(legal_sha+'.txt') else (_ for _ in ()).throw(FileNotFoundError()))
    return row,legal


def declarations(directory,receipt,index,base_components,origin,generation):
    if type(generation) is not int or not 1<=generation<2**53:raise ValueError('Explicit monotonic generation required')
    source=source_line(origin);repository={'id':'toddy-native','sources_sha256':hashlib.sha256(source).hexdigest(),
        'inrelease_sha256':p.digest(Path(directory)/'InRelease'),'inrelease_bytes':(Path(directory)/'InRelease').stat().st_size}
    items={row['name']:row for row in receipt['packages']};base={row['name']:row for row in base_components}
    if len(base)!=len(base_components) or set(base)&set(ORDER) or not set(ORDER)<=set(items):raise ValueError('Separate offline base and all four curated archives required')
    if any(name not in items or any(items[name].get(key)!=row.get(key) for key in ('version','architecture','archive_sha256','component_record_sha256')) for name,row in base.items()):raise ValueError('Offline base differs from verified repository')
    metadata_rows={name:{'version':row['version'],'depends':index[name].get('Depends',''),'pre_depends':index[name].get('Pre-Depends','')} for name,row in items.items()}
    files={'toddy-native.list':source};reviewed={}
    for name in ORDER:
        row=items[name];archive=p.regular(Path(directory)/row['asset']);control,payload,installed_bytes=p.archive_contents(archive)
        if p.digest(archive)!=row['archive_sha256'] or installed_bytes!=row['installed_bytes'] or (control.get('Package'),control.get('Version'),control.get('Architecture'))!=(name,row['version'],row['architecture']):raise ValueError('Actual curated archive changed')
        expected={virtual:payload.get(virtual,{}).get('sha256') for virtual,owner in POSTCONDITIONS.items() if owner==name}
        if row['postconditions']!=expected or any(not p.HASH.fullmatch(value or '') for value in expected.values()):raise ValueError('Actual curated vital path ownership differs')
        reviewed[name]=row
    for release_id,names in RELEASE_PACKAGES.items():
        selected=p.dependency_closure(metadata_rows,names)
        if selected-set(base)!=names:raise ValueError('Curated closure requires packages outside reviewed installed base/set')
        packages=[reviewed[name] for name in ORDER if name in names]
        row,legal=release_declaration(release_id,packages,generation,origin);legal_sha=row['terms_sha256']
        files['native-terms-'+legal_sha+'.txt']=legal
        files['candidate-'+release_id+'.json']=_encode({'version':1,'generation':generation,'repository':repository,'release':row})+b'\n'
    return files,repository


def write(output,files,receipt,repository,generation):
    output=Path(output)
    if not output.is_absolute() or output.resolve()!=output or os.path.lexists(output) or not output.parent.is_dir():raise ValueError('New canonical declaration generation required')
    output.mkdir(mode=0o700);hashes={}
    for name,data in files.items():
        if not re.fullmatch('[A-Za-z0-9_.+-]+',name):raise ValueError('Flat declaration asset required')
        with (output/name).open('xb') as stream:os.fchmod(stream.fileno(),0o644);stream.write(data);stream.flush();os.fsync(stream.fileno())
        hashes[name]=p.digest(output/name)
    result={'version':1,'kind':'unsigned-curated-component-declarations','generation':generation,'repository':repository,
        'issued_unix':receipt['issued_unix'],'expires_unix':receipt['expires_unix'],'files':hashes,
        'producer_sha256':p.digest(__file__),'parent_signed_repository_verified':True,'signatures_created':False,
        'qualification_created':False,'production_catalog_created':False,'published':False,
        'install_map':{'toddy-native.list':'/etc/apt/sources.list.d/toddy-native.list',
            **{name:str(DIRECTORY/'terms'/(name.removeprefix('native-terms-'))) for name in files if name.startswith('native-terms-')}}}
    with (output/'declarations-export.json').open('xb') as stream:os.fchmod(stream.fileno(),0o644);stream.write(p.encoded(result));stream.flush();os.fsync(stream.fileno())
    descriptor=os.open(output,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--repository',type=Path,required=True);parser.add_argument('--base-projection',type=Path,required=True)
    parser.add_argument('--additional-components',type=Path,required=True);parser.add_argument('--origin',required=True)
    parser.add_argument('--generation',type=int,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();trust=metadata.public_trust();receipt,index=verified_repository(args.repository,trust)
    base=p.strict(p.regular(args.base_projection).read_bytes())['components']
    additions=p.strict(p.regular(args.additional_components).read_bytes())
    if not isinstance(additions,list) or {row.get('name') for row in additions}!=p.MANDATORY_ADDITIONS:raise ValueError('Exact offline base additions required')
    files,repo=declarations(args.repository,receipt,index,[*base,*additions],args.origin,args.generation)
    result=write(args.output,files,receipt,repo,args.generation)
    print(p.encoded({'state':result['kind'],'catalog_created':False,'qualification_created':False,'published':False}).decode(),end='')


if __name__=='__main__':main()
