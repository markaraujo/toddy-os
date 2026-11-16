#!/usr/bin/env python3
"""Offline Phase2 release custody and portal handoff; never uploads or publishes."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=Path('config/phase2/public-release.json')
BASE='https://github.com/markaraujo/toddy-os/releases/'
ROLES={'iso','checksums','source','inventory','guide','build-guide','recovery','licenses'}
CHECKS={'installed-boot','install','credential-privilege','cancel-replay','recovery','offline-base','acquired-experience','hygiene','browser','profile-harness','bios-installed-detached-boot','uefi-installed-detached-boot','native-acquisition-full-flow','owner-setup','source-license-inventory'}
HASH=re.compile('[a-f0-9]{64}\\Z');COMMIT=re.compile('[a-f0-9]{40}\\Z')
NAME=re.compile('[A-Za-z0-9][A-Za-z0-9._-]{0,119}\\Z')
TAG=re.compile('v0\\.[0-9][A-Za-z0-9._-]{0,79}\\Z')


def strict(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate release JSON key')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite release JSON')))


def read(path,maximum=4*1024**2):
    path=Path(path)
    if path.resolve()!=path or not path.is_file() or path.is_symlink() or path.stat().st_size>maximum:raise ValueError('Canonical bounded release input required')
    return path.read_bytes()


def hash_file(path):
    path=Path(path)
    if not path.is_absolute() or path.resolve()!=path or not path.is_file() or path.is_symlink():raise ValueError('Canonical local artifact required')
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno());digest=hashlib.file_digest(stream,'sha256').hexdigest();after=os.fstat(stream.fileno())
    if before.st_size<=0 or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise ValueError('Artifact changed during hashing')
    return digest,before.st_size


def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.PIPE).strip()


def evidence(root,relative,expected):
    path=Path(relative)
    if not isinstance(relative,str) or not relative.startswith('docs/evidence/') or path.is_absolute() or '..' in path.parts:raise ValueError('Retained release evidence path')
    git(root,'ls-files','--error-unmatch','--',relative)
    raw=read(root/path)
    if not HASH.fullmatch(expected) or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Retained release evidence changed')
    return strict(raw)


def acceptance_state(root,reference):
    status=strict(read(root/'status.json'))
    rows={row['id']:row for row in status['milestones']}
    if status.get('owner_review',{}).get('phase_2_approved') is not True or any(rows.get('B%02d'%i,{}).get('status')!='completed' for i in range(1,13)):raise ValueError('Owner authorization and actual completed B01-B12 required')
    if set(reference)!={'path','sha256'} or reference['path'] not in rows['B13'].get('evidence',[]):raise ValueError('G2 evidence must be retained by B13')
    pair=(rows.get('B13',{}).get('status'),status['gates']['G2'])
    if pair==('in_progress','pending'):return 'delivery-in-progress'
    if pair==('completed','passed'):return 'finished-release'
    raise ValueError('B13/G2 delivery state must remain consistent')


def require_delivery_in_progress(root,reference):
    if strict(read(root/'status.json')).get('execution_hold'):raise ValueError('Owner execution hold prevents a new release handoff')
    if acceptance_state(root,reference)!='delivery-in-progress':raise ValueError('New handoff requires B13 in_progress and G2 pending; finished release is immutable')


def gate(root,reference,iso,source_commit,inventory):
    acceptance_state(root,reference)
    receipt=evidence(root,reference['path'],reference['sha256'])
    if (set(receipt)!={'version','gate','state','source_commit','iso','native_checks','physical_validation','experimental_preview','native_package_manifest'} or type(receipt['version']) is not int or receipt['version']!=1 or receipt['gate']!='G2' or receipt['state']!='technical-passed-delivery-pending' or receipt['source_commit']!=source_commit or receipt['iso']!={'sha256':iso['sha256'],'bytes':iso['bytes']} or receipt['physical_validation']!='pending' or receipt['experimental_preview'] is not True or set(receipt['native_checks'])!=CHECKS):raise ValueError('Candidate-bound native G2 receipt required')
    for check,row in receipt['native_checks'].items():
        if not isinstance(row,dict) or set(row)!={'state','path','sha256'} or row['state']!='passed':raise ValueError('Unpassed required native G2 check')
        actual=evidence(root,row['path'],row['sha256'])
        if not isinstance(actual,dict) or actual.get('final_iso')!=receipt['iso'] or actual.get('source_commit')!=source_commit or actual.get('native_guest') is not True or actual.get('all_required_checks_passed') is not True:raise ValueError('Native check must bind this final ISO/source, not prior component or draft evidence')
        if check in ('bios-installed-detached-boot','uefi-installed-detached-boot'):
            if actual.get('firmware')!=check.split('-')[0] or actual.get('installed_boot') is not True or actual.get('installation_media_detached') is not True:raise ValueError('Actual BIOS/UEFI installed boot with media detached required')
        if check=='native-acquisition-full-flow':
            guard=actual.get('native_acquisition_guard',{})
            if set(guard)!={'script_sha256','exit','result'} or guard['script_sha256']!=hashlib.sha256(read(root/'scripts/qualification/native_acquisition_release_guard.py')).hexdigest() or type(guard['exit']) is not int or guard['exit']!=0 or not isinstance(guard['result'],dict) or guard['result'].get('all_advertised_entries_full_flow') is not True or guard['result'].get('expected_public_trust_matched') is not True:raise ValueError('Actual full-flow native acquisition release guard required')
    pinned=receipt['native_package_manifest']
    if not isinstance(pinned,dict) or set(pinned)!={'path','sha256'} or pinned['sha256']!=inventory['sha256']:raise ValueError('Attached component inventory must match native package pins')
    packages=evidence(root,pinned['path'],pinned['sha256'])
    components=packages.get('components') if isinstance(packages,dict) else None
    if not isinstance(components,list) or not components:raise ValueError('Native package/component pins required')
    names=set()
    for component in components:
        if not isinstance(component,dict) or not isinstance(component.get('name'),str) or component['name'] in names or not isinstance(component.get('version'),str) or not component['version'] or any(not isinstance(component.get(key),str) or not HASH.fullmatch(component[key]) for key in ('archive_sha256','component_record_sha256','recipe_sha256')):raise ValueError('Native package/component identity missing')
        sources=component.get('sources')
        if not isinstance(sources,list) or any(not isinstance(source,dict) or not isinstance(source.get('filename'),str) or not isinstance(source.get('sha256'),str) or not HASH.fullmatch(source['sha256']) for source in sources):raise ValueError('Native component source pins missing')
        names.add(component['name'])


def identity(value):
    if not isinstance(value.get('tag'),str) or not TAG.fullmatch(value['tag']) or not any(word in value['tag'] for word in ('phase2','preview')) or not isinstance(value.get('source_commit'),str) or not COMMIT.fullmatch(value['source_commit']) or value.get('release_url')!=BASE+'tag/'+value['tag']:raise ValueError('Explicit experimental tag/source/release URL required')


def asset_rows(rows,tag,*,local=False):
    if not isinstance(rows,list) or not 8<=len(rows)<=256:raise ValueError('Complete release artifact set required')
    names=set();roles=[]
    for row in rows:
        fields={'role','name','url','sha256','bytes'}|({'path'} if local else set())
        if not isinstance(row,dict) or set(row)!=fields or row['role'] not in ROLES or not isinstance(row['name'],str) or not NAME.fullmatch(row['name']) or row['name'] in names or row['url']!=BASE+'download/'+tag+'/'+row['name'] or not isinstance(row['sha256'],str) or not HASH.fullmatch(row['sha256']) or type(row['bytes']) is not int or row['bytes']<=0:raise ValueError('Release artifact identity/hash/URL')
        names.add(row['name']);roles.append(row['role'])
    if set(roles)!=ROLES or roles.count('iso')!=1 or roles.count('checksums')!=1:raise ValueError('Required release artifact roles')


def checksum_and_iso(assets):
    iso=next(row for row in assets if row['role']=='iso')
    with Path(iso['path']).open('rb') as stream:
        stream.seek(32769)
        if stream.read(5)!=b'CD001':raise ValueError('Actual ISO9660 volume descriptor required')
    checksum=next(row for row in assets if row['role']=='checksums')
    lines=read(Path(checksum['path'])).decode('ascii').splitlines();parsed={}
    for line in lines:
        match=re.fullmatch('([a-f0-9]{64}) [ *]([A-Za-z0-9][A-Za-z0-9._-]{0,119})',line)
        if not match or match[2] in parsed:raise ValueError('Canonical release SHA256SUMS required')
        parsed[match[2]]=match[1]
    if parsed!={row['name']:row['sha256'] for row in assets if row['role']!='checksums'}:raise ValueError('SHA256SUMS must list exactly the attached non-checksum assets')


def prepare(root,request):
    if set(request)!={'version','tag','source_commit','release_url','g2_evidence','artifacts'} or type(request['version']) is not int or request['version']!=1:raise ValueError('Release request schema')
    identity(request);require_delivery_in_progress(root,request['g2_evidence'])
    if git(root,'status','--porcelain'):raise ValueError('Commit reviewed release inputs first')
    if git(root,'rev-parse','refs/tags/'+request['tag']+'^{commit}')!=request['source_commit']:raise ValueError('Actual immutable local tag differs from accepted source')
    assets=[]
    for row in request['artifacts']:
        if set(row)!={'role','path','url'}:raise ValueError('Explicit local artifact and URL required')
        path=Path(row['path']);digest,size=hash_file(path)
        assets.append(dict(row,name=path.name,sha256=digest,bytes=size))
    asset_rows(assets,request['tag'],local=True)
    checksum_and_iso(assets)
    iso=next(row for row in assets if row['role']=='iso')
    gate(root,request['g2_evidence'],iso,request['source_commit'],next(row for row in assets if row['role']=='inventory'))
    return {'version':1,'state':'prepared-publication-unverified','tag':request['tag'],'source_commit':request['source_commit'],'release_url':request['release_url'],'g2_evidence':request['g2_evidence'],'artifacts':assets,'experimental_preview':True,'physical_validation':'pending'}


def github_assets(release,assets):
    uploaded=release.get('assets',[])
    if len(uploaded)!=len(assets) or len({row['name'] for row in uploaded})!=len(uploaded):raise ValueError('Public release artifact set differs')
    by_name={row['name']:row for row in uploaded}
    for row in assets:
        actual=by_name.get(row['name'],{})
        if actual.get('size')!=row['bytes'] or actual.get('digest')!='sha256:'+row['sha256'] or actual.get('state')!='uploaded' or actual.get('browser_download_url')!=row['url']:raise ValueError('Actual GitHub asset size/digest/URL differs')


def promote(root,prepared,response_path,downloads):
    if set(prepared)!={'version','state','tag','source_commit','release_url','g2_evidence','artifacts','experimental_preview','physical_validation'} or type(prepared['version']) is not int or prepared['version']!=1 or prepared['state']!='prepared-publication-unverified' or prepared['experimental_preview'] is not True or prepared['physical_validation']!='pending':raise ValueError('Prepared release manifest required')
    identity(prepared);asset_rows(prepared['artifacts'],prepared['tag'],local=True);require_delivery_in_progress(root,prepared['g2_evidence'])
    # Recheck original local bytes and the actual tag after the publication wait.
    for row in prepared['artifacts']:
        if hash_file(Path(row['path']))!=(row['sha256'],row['bytes']):raise ValueError('Original release artifact changed')
    checksum_and_iso(prepared['artifacts'])
    if git(root,'rev-parse','refs/tags/'+prepared['tag']+'^{commit}')!=prepared['source_commit']:raise ValueError('Release tag changed')
    iso=next(row for row in prepared['artifacts'] if row['role']=='iso');gate(root,prepared['g2_evidence'],iso,prepared['source_commit'],next(row for row in prepared['artifacts'] if row['role']=='inventory'))
    response_raw=read(response_path);relative=Path(response_path).relative_to(root).as_posix()
    release=evidence(root,relative,hashlib.sha256(response_raw).hexdigest())
    if release.get('draft') is not False or release.get('prerelease') is not True or release.get('tag_name')!=prepared['tag'] or release.get('html_url')!=prepared['release_url'] or type(release.get('id')) is not int or release['id']<=0:raise ValueError('Retained actual public GitHub prerelease required')
    github_assets(release,prepared['artifacts'])
    for row in prepared['artifacts']:
        download=Path(downloads)/row['name']
        if download.samefile(row['path']) or hash_file(download)!=(row['sha256'],row['bytes']):raise ValueError('Independent public-route download verification required')
    return {'version':1,'state':'public-prerelease-assets-verified','tag':prepared['tag'],'source_commit':prepared['source_commit'],'release_url':prepared['release_url'],'g2_evidence':prepared['g2_evidence'],
        'artifacts':[{key:value for key,value in row.items() if key!='path'} for row in prepared['artifacts']],
        'experimental_preview':True,'physical_validation':'pending','github_evidence':{'path':relative,'sha256':hashlib.sha256(response_raw).hexdigest()},'pages_handoff':'pending-deployment-verification'}


def public_metadata(root):
    path=root/PUBLIC
    if not path.exists():return None
    value=strict(read(path))
    if set(value)!={'version','state','tag','source_commit','release_url','g2_evidence','artifacts','experimental_preview','physical_validation','github_evidence','pages_handoff'} or type(value['version']) is not int or value['version']!=1 or value['state']!='public-prerelease-assets-verified' or value['experimental_preview'] is not True or value['physical_validation']!='pending' or value['pages_handoff']!='pending-deployment-verification':raise ValueError('Public preview metadata schema')
    identity(value);asset_rows(value['artifacts'],value['tag']);gate(root,value['g2_evidence'],next(row for row in value['artifacts'] if row['role']=='iso'),value['source_commit'],next(row for row in value['artifacts'] if row['role']=='inventory'))
    release=evidence(root,value['github_evidence']['path'],value['github_evidence']['sha256'])
    if release.get('draft') is not False or release.get('prerelease') is not True or release.get('tag_name')!=value['tag'] or release.get('html_url')!=value['release_url']:raise ValueError('Public release evidence differs')
    github_assets(release,value['artifacts'])
    return value


def portal(root,page):
    value=public_metadata(root)
    if value is None:return page
    esc=html.escape;assets=value['artifacts']
    start=page.index('            <section class="download section-wrap" id="download">');end=page.index('            </section>',start)+len('            </section>')
    titles={'iso':'Phase 2 preview ISO ↗','checksums':'Checksums ↗','source':'Corresponding source ↗','inventory':'Component inventory ↗','guide':'Owner guide ↗','build-guide':'Build guide ↗','recovery':'Recovery guide ↗','licenses':'Licenses ↗'}
    links=''.join('<a class="'+('button primary' if row['role']=='iso' else 'text-link')+'" href="'+esc(row['url'],quote=True)+'">'+titles[row['role']]+'</a>' for row in assets)
    old=BASE+'tag/v0.1.0-foundation.1'
    fragment='''            <section class="download section-wrap" id="download">
                <span class="anchor-target" id="releases"></span>
                <div><p class="eyebrow">Releases / experimental preview</p>
                    <h2>Try the current version.<br />Start in a virtual machine.</h2>
                    <p>Phase 2 experimental preview tested in the native guest. Review the owner guide and evidence before installation.</p>
                    <div class="release-tags"><span data-no-translate>'''+esc(value['tag'])+'''</span><span>Experimental preview</span><span>VM-tested</span></div>
                </div><div class="download-actions">'''+links+'<a class="text-link" href="'+esc(value['release_url'])+'">Release notes ↗</a><a class="text-link" href="'+BASE+'">All releases & release notes ↗</a><a class="text-link" href="'+old+'">Foundation release & checksums ↗</a><a class="text-link" href="../'+esc(value['g2_evidence']['path'])+'">Native validation evidence ↗</a><small>Final native guest checks passed. Physical hardware validation pending.</small></div>\n            </section>'
    return page[:start]+fragment+page[end:]


def write_new(path,value):
    path=Path(path)
    if not path.is_absolute() or path.parent.resolve()!=path.parent:raise ValueError('Canonical release output path')
    with path.open('x',encoding='utf-8') as stream:
        os.fchmod(stream.fileno(),0o600);json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    stage=commands.add_parser('prepare');stage.add_argument('--request',type=Path,required=True);stage.add_argument('--output',type=Path,required=True)
    publish=commands.add_parser('promote');publish.add_argument('--prepared',type=Path,required=True);publish.add_argument('--github-response',type=Path,required=True);publish.add_argument('--downloads',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='prepare':write_new(args.output,prepare(ROOT,strict(read(args.request))))
    else:
        result=promote(ROOT,strict(read(args.prepared)),args.github_response,args.downloads)
        write_new(ROOT/PUBLIC,result)
        subprocess.run(['make','dashboard'],cwd=ROOT,check=True);subprocess.run(['make','site'],cwd=ROOT,check=True)
        print('Local portal regenerated. Public Pages deployment verification remains pending.')


if __name__=='__main__':main()
