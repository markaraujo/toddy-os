#!/usr/bin/env python3
"""Offline package-only prerelease custody; never signs, uploads or enables Setup."""
import argparse
import hashlib
import html
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/build/phase2')]
import phase2_release as common
import acquisition_declarations as declarations
import archive_metadata
import package_sources
import package_sources_reviewed

PUBLIC=Path('config/phase2/public-package-release.json')
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9._+-]{0,159}\Z')
ROLES={'repository','source','project-source','inventory','licenses','guide','checksums'}
MAX_ASSETS=1000
MAX_ASSET_BYTES=2*1024**3
PENDING={'iso':'not-included','g2':'pending','native_acquisition':'not-advertised','physical_validation':'pending'}


def identity(value):
    common.identity(value)
    if not re.fullmatch(r'v0\.[0-9]+\.0-preview\.[1-9][0-9]*',value['tag']):raise ValueError('Explicit experimental package preview tag required')


def authorization(root):
    status=common.strict(common.read(root/'status.json'))
    if status.get('owner_review',{}).get('phase_2_approved') is not True or status.get('execution_hold'):raise ValueError('Active owner-authorized Phase2 required')


def asset_count(rows):
    if not isinstance(rows,list) or not 10<=len(rows)<=MAX_ASSETS:raise ValueError('Complete package assets required within GitHub1000-asset release limit')


def checked_hash(path):
    path=Path(path)
    if not path.is_absolute() or path.resolve()!=path or not path.is_file() or path.is_symlink():raise ValueError('Canonical local package asset required')
    if not 0<path.stat().st_size<MAX_ASSET_BYTES:raise ValueError('GitHub release asset must be strictly below2GiB')
    return common.hash_file(path)


def assets(rows,tag,*,local=False):
    asset_count(rows)
    seen=set();counts={key:0 for key in ROLES}
    for row in rows:
        if not isinstance(row,dict) or set(row)!=({'role','name','url','sha256','bytes'}|({'path'} if local else set())) or row['role'] not in ROLES or not NAME.fullmatch(row.get('name','')) or row['name'] in seen or row['url']!=common.BASE+'download/'+tag+'/'+row['name'] or not common.HASH.fullmatch(row.get('sha256','')) or type(row['bytes']) is not int or not 0<row['bytes']<MAX_ASSET_BYTES:raise ValueError('Exact flat package asset identity and GitHub below2GiB limit required')
        if row['name'].lower().endswith(('.iso','.img','.qcow2')):raise ValueError('Package-only release cannot include installation media')
        seen.add(row['name']);counts[row['role']]+=1
    if not all(counts.values()) or counts['checksums']!=1 or counts['guide']!=1 or counts['project-source']!=1 or counts['inventory']!=1:raise ValueError('Package/source/legal/guide/checksum roles required')


def checksums(rows):
    checksum=next(row for row in rows if row['role']=='checksums');parsed={}
    if checksum['name']!='SHA256SUMS':raise ValueError('Explicit SHA256SUMS required')
    for line in common.read(Path(checksum['path'])).decode('ascii').splitlines():
        match=re.fullmatch(r'([a-f0-9]{64}) [ *]([A-Za-z0-9][A-Za-z0-9._+-]{0,159})',line)
        if not match or match[2] in parsed:raise ValueError('Canonical exact package SHA256SUMS required')
        parsed[match[2]]=match[1]
    if parsed!={row['name']:row['sha256'] for row in rows if row['role']!='checksums'}:raise ValueError('Package SHA256SUMS must bind every other attached asset exactly')


def repository(directory,rows):
    selected=list(Path(directory).iterdir())
    if len(selected)>MAX_ASSETS:raise ValueError('Actual repository exceeds GitHub1000-asset release limit')
    for path in selected:
        if path.is_file() and path.stat().st_size>=MAX_ASSET_BYTES:raise ValueError('Actual repository asset must be strictly below2GiB')
    receipt,_index=declarations.verified_repository(directory,archive_metadata.public_trust())
    for package in receipt['packages']:
        archive=Path(directory)/package['asset'];control,body,_size=declarations.p.archive_contents(archive)
        if (control.get('Package'),control.get('Version'),control.get('Architecture'),control.get('Depends',''))!=(package['name'],package['version'],package['architecture'],package['depends']):raise ValueError('Actual native package archive control differs')
        for field in ('copyright','source_notices_index'):
            legal=package.get(field)
            if legal and body.get(legal['path'],{}).get('sha256')!=legal['sha256']:raise ValueError('Actual native package legal ownership differs')
        legal_files,names=archive_metadata.legal_assets(archive,package)
        if names!=package['legal_assets'] or any(common.read(Path(directory)/name,maximum=64*1024**2)!=data for name,data in legal_files.items()):raise ValueError('Exact exported legal bytes differ from native archive')
    actual={path.name:checked_hash(path) for path in Path(directory).iterdir()}
    expected={row['name']:(row['sha256'],row['bytes']) for row in rows if row['role']=='repository'}
    if actual!=expected:raise ValueError('All exact signed flat repository assets must be attached')
    return {'archive_export_sha256':actual['archive-export.json'][0],
        'inrelease_sha256':actual['InRelease'][0],'public_keyring_sha256':receipt['public_keyring_sha256'],
        'public_fingerprint':receipt['public_fingerprint'],'packages':[{key:row[key] for key in ('name','version','architecture','archive_sha256','component_record_sha256','recipe_sha256')} for row in receipt['packages']]}


def source_review(root,reference,rows,pins,commit):
    if not isinstance(reference,dict) or set(reference)!={'path','sha256'}:raise ValueError('Retained source/license review required')
    review=common.evidence(root,reference['path'],reference['sha256'])
    if isinstance(review,dict) and review.get('kind')==package_sources_reviewed.KIND:
        package_sources_reviewed.validate_acceptance(root,review,rows,pins,commit)
        return review
    if not isinstance(review,dict) or set(review)!={'version','scope','source_commit','packages','source_assets','project_source_assets','inventory_assets','license_assets','reviewed'} or type(review['version']) is not int or review['version']!=1 or review['scope']!='native-package-source-license-review' or review['source_commit']!=commit or review['packages']!=pins['packages'] or review['reviewed'] is not True:raise ValueError('Exact source/legal review of the actual native package set required')
    for role,field in (('source','source_assets'),('project-source','project_source_assets'),('inventory','inventory_assets'),('licenses','license_assets')):
        if review[field]!=[{key:row[key] for key in ('name','sha256','bytes')} for row in rows if row['role']==role]:raise ValueError('Reviewed corresponding-source/license assets differ')


def verify_source_assets(root,reference,rows,pins,commit,repository_directory):
    reviewed=source_review(root,reference,rows,pins,commit)
    inventory=next(row['path'] for row in rows if row['role']=='inventory')
    if reviewed is not None:
        return package_sources_reviewed.verify_assets(root,inventory,rows,pins,commit,reviewed,repository_directory)
    return package_sources.verify_assets(inventory,rows,pins,commit)


def prepare(root,request):
    if not isinstance(request,dict) or set(request)!={'version','tag','source_commit','release_url','repository_directory','source_review','artifacts'} or type(request['version']) is not int or request['version']!=1:raise ValueError('Package-only release request schema')
    asset_count(request['artifacts'])
    identity(request);authorization(root)
    if common.git(root,'status','--porcelain'):raise ValueError('Commit reviewed release inputs first')
    if common.git(root,'rev-parse','refs/tags/'+request['tag']+'^{commit}')!=request['source_commit']:raise ValueError('Actual package prerelease tag/source differs')
    rows=[]
    for row in request['artifacts']:
        if not isinstance(row,dict) or set(row)!={'role','path','url'}:raise ValueError('Explicit local public asset required')
        path=Path(row['path']);digest,size=checked_hash(path)
        rows.append(dict(row,name=path.name,sha256=digest,bytes=size))
    assets(rows,request['tag'],local=True);checksums(rows)
    pins=repository(Path(request['repository_directory']),rows)
    verify_source_assets(root,request['source_review'],rows,pins,request['source_commit'],Path(request['repository_directory']))
    return {'version':1,'state':'package-publication-unverified',**{key:request[key] for key in ('tag','source_commit','release_url','repository_directory','source_review')},'artifacts':rows,'repository_pins':pins,'scope':'experimental-native-package-artifacts','limitations':PENDING}


def validate(value,*,prepared=False):
    fields={'version','state','tag','source_commit','release_url','source_review','artifacts','repository_pins','scope','limitations'}|({'repository_directory'} if prepared else {'github_evidence','pages_handoff'})
    if not isinstance(value,dict) or set(value)!=fields or type(value['version']) is not int or value['version']!=1 or value['state']!=('package-publication-unverified' if prepared else 'public-package-assets-verified') or value['scope']!='experimental-native-package-artifacts' or value['limitations']!=PENDING:raise ValueError('Explicit package-only prerelease scope required')
    identity(value);assets(value['artifacts'],value['tag'],local=prepared)
    pins=value['repository_pins']
    if not isinstance(pins,dict) or set(pins)!={'archive_export_sha256','inrelease_sha256','public_keyring_sha256','public_fingerprint','packages'} or not isinstance(pins['packages'],list) or not pins['packages']:raise ValueError('Exact signed native repository pins required')
    names=set()
    for package in pins['packages']:
        if not isinstance(package,dict) or set(package)!={'name','version','architecture','archive_sha256','component_record_sha256','recipe_sha256'} or not isinstance(package['name'],str) or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*',package['name']) or package['name'] in names or not isinstance(package['version'],str) or not re.fullmatch(r'[0-9][A-Za-z0-9.+:~_-]{0,95}',package['version']) or package['architecture'] not in ('amd64','all') or any(not isinstance(package[key],str) or not common.HASH.fullmatch(package[key]) for key in ('archive_sha256','component_record_sha256','recipe_sha256')):raise ValueError('Native package provenance pin schema')
        names.add(package['name'])
    if not re.fullmatch(r'[A-F0-9]{40}|[A-F0-9]{64}',pins.get('public_fingerprint','')):raise ValueError('Independent public fingerprint required')
    by_name={row['name']:row['sha256'] for row in value['artifacts'] if row['role']=='repository'}
    if by_name.get('archive-export.json')!=pins['archive_export_sha256'] or by_name.get('InRelease')!=pins['inrelease_sha256'] or by_name.get('archive-keyring.gpg')!=pins['public_keyring_sha256']:raise ValueError('Public repository asset pins differ')


def promote(root,prepared,response,downloads):
    validate(prepared,prepared=True);authorization(root)
    for row in prepared['artifacts']:
        if checked_hash(Path(row['path']))!=(row['sha256'],row['bytes']):raise ValueError('Original package asset changed')
    checksums(prepared['artifacts'])
    if repository(Path(prepared['repository_directory']),prepared['artifacts'])!=prepared['repository_pins']:raise ValueError('Signed repository changed')
    verify_source_assets(root,prepared['source_review'],prepared['artifacts'],prepared['repository_pins'],prepared['source_commit'],Path(prepared['repository_directory']))
    if common.git(root,'rev-parse','refs/tags/'+prepared['tag']+'^{commit}')!=prepared['source_commit']:raise ValueError('Package tag changed')
    relative=Path(response).relative_to(root).as_posix();raw=common.read(response)
    release=common.evidence(root,relative,hashlib.sha256(raw).hexdigest())
    actual_release(release,prepared)
    for row in prepared['artifacts']:
        path=Path(downloads)/row['name']
        if path.samefile(row['path']) or checked_hash(path)!=(row['sha256'],row['bytes']):raise ValueError('Independent public-route package download required')
    result={key:value for key,value in prepared.items() if key not in ('repository_directory','state','artifacts')}
    result.update(state='public-package-assets-verified',artifacts=[{key:value for key,value in row.items() if key!='path'} for row in prepared['artifacts']],github_evidence={'path':relative,'sha256':hashlib.sha256(raw).hexdigest()},pages_handoff='pending-deployment-verification')
    return result


def actual_release(release,value):
    if release.get('draft') is not False or release.get('prerelease') is not True or release.get('tag_name')!=value['tag'] or release.get('html_url')!=value['release_url'] or type(release.get('id')) is not int or release['id']<=0:raise ValueError('Actual published package prerelease required')
    common.github_assets(release,value['artifacts'])


def public_metadata(root):
    path=root/PUBLIC
    if not path.exists():return None
    value=common.strict(common.read(path));validate(value)
    trust=common.strict(common.read(root/'config/phase2/archive-public-trust.json'))
    if value['repository_pins']['public_fingerprint']!=trust.get('fingerprint') or value['repository_pins']['public_keyring_sha256']!=trust.get('public_keyring_sha256'):raise ValueError('Published package public trust differs from independent pins')
    if value['pages_handoff']!='pending-deployment-verification':raise ValueError('Package Pages handoff schema')
    source_review(root,value['source_review'],value['artifacts'],value['repository_pins'],value['source_commit'])
    actual_release(common.evidence(root,value['github_evidence']['path'],value['github_evidence']['sha256']),value)
    return value


def portal(root,page):
    value=public_metadata(root)
    if value is None:return page
    esc=html.escape
    titles={'guide':'Package testing guide ↗','source':'Corresponding source ↗','project-source':'Corresponding source ↗','inventory':'Component inventory ↗','licenses':'Licenses ↗','checksums':'Checksums ↗'}
    links=''.join('<a class="text-link" href="'+esc(row['url'],quote=True)+'">'+titles[row['role']]+'</a>' for row in value['artifacts'] if row['role'] in titles)
    block='<section class="download section-wrap" id="package-preview"><div><p class="eyebrow">Experimental package artifacts</p><h2>Native packages for qualification.</h2><p>Package repository artifacts only. Desktop ISO, G2 and installed-user acquisition qualification are pending.</p><span data-no-translate>'+esc(value['tag'])+'</span></div><div class="download-actions">'+links+'<a class="text-link" href="'+esc(value['release_url'],quote=True)+'">Package release notes ↗</a><small>For disposable Toddy test systems. Downloading packages does not activate AI or grant administration.</small></div></section>'
    marker='            <section class="download section-wrap" id="download">'
    if page.count(marker)!=1:raise ValueError('Unique existing download section required')
    return page.replace(marker,block+'\n'+marker,1)


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);commands=parser.add_subparsers(dest='action',required=True)
    draft=commands.add_parser('prepare');draft.add_argument('--request',type=Path,required=True);draft.add_argument('--output',type=Path,required=True)
    final=commands.add_parser('promote');final.add_argument('--prepared',type=Path,required=True);final.add_argument('--github-response',type=Path,required=True);final.add_argument('--downloads',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='prepare':
        prepared=prepare(ROOT,common.strict(common.read(args.request)));common.write_new(args.output,prepared)
        print('Package-only local preflight: '+str(len(prepared['artifacts']))+' assets; largest '+str(max(row['bytes'] for row in prepared['artifacts']))+' bytes; publication unverified.')
    else:
        common.write_new(ROOT/PUBLIC,promote(ROOT,common.strict(common.read(args.prepared)),args.github_response,args.downloads))
        subprocess.run(['make','dashboard'],cwd=ROOT,check=True);subprocess.run(['make','site'],cwd=ROOT,check=True)
        print('Package-only portal regenerated; actual Pages deployment verification pending.')


if __name__=='__main__':main()
