#!/usr/bin/python3 -I
"""Export unsigned flat native APT assets; no signing, install or publication."""
import argparse
from datetime import datetime,timezone
from email.utils import format_datetime
import gzip
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(HERE)]
import offline_payload as p
from image_projection import original_source_provenance
from runtime.setup.releases import PACKAGES,POSTCONDITIONS
from runtime.shared.openpgp import public_key_only

PUBLIC_KEY=ROOT/'config/phase2/archive-public-key.gpg'
PUBLIC_PINS=ROOT/'config/phase2/archive-public-trust.json'
HOST_RESERVE=100*1024**3+512*1024**2
NATIVE_RESERVE=16*1024**3+512*1024**2
MAX_VALIDITY=31*24*3600


def public_trust(key=PUBLIC_KEY,pins=PUBLIC_PINS):
    """Only a pinned public certificate; isolated GPG never sees owner keyrings."""
    key=p.regular(key);pins=p.regular(pins)
    if not 0<key.stat().st_size<=1048576 or not 0<pins.stat().st_size<=65536:raise ValueError('Bounded public certificate/pins required')
    value=p.strict(pins.read_bytes());data=key.read_bytes()
    if value.get('version')!=1 or value.get('public_keyring')!='config/phase2/archive-public-key.gpg' or value.get('algorithm')!='Ed25519' or hashlib.sha256(data).hexdigest()!=value.get('public_keyring_sha256') or not re.fullmatch('[A-F0-9]{40}|[A-F0-9]{64}',value.get('fingerprint','')):
        raise ValueError('Independent public archive pins differ')
    if not 0<len(data)<=1048576:raise ValueError('Bounded public certificate required')
    public_key_only(data)
    with tempfile.TemporaryDirectory(prefix='toddy-public-certificate-') as directory:
        public=Path(directory)/'public.gpg';public.write_bytes(data)
        result=subprocess.run(['/usr/bin/gpg','--no-options','--homedir',directory,'--batch','--no-auto-key-retrieve',
            '--no-auto-key-import','--with-colons','--fingerprint','--show-keys',str(public)],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env={'PATH':'/usr/bin:/bin','HOME':directory,'LC_ALL':'C'},timeout=10)
        if result.returncode or len(result.stdout)>65536:raise ValueError('Public certificate inspection failed')
        rows=[line.split(':') for line in result.stdout.decode('ascii',errors='strict').splitlines()]
        primaries=[row for row in rows if row[0]=='pub']
        primary_fingerprints=[];awaiting=False
        for row in rows:
            if row[0]=='pub':awaiting=True
            elif row[0]=='fpr' and awaiting:primary_fingerprints.append(row[9]);awaiting=False
        if len(primaries)!=1 or primary_fingerprints!=[value['fingerprint']] or primaries[0][3]!='22' or primaries[0][1] in ('e','r','d') or not primaries[0][5].isdigit() or not primaries[0][6].isdigit() or int(primaries[0][5])!=value.get('created_unix') or int(primaries[0][6])!=value.get('expires_unix'):
            raise ValueError('Actual public certificate identity/lifetime differs')
    if key.read_bytes()!=data:raise ValueError('Public source certificate changed during inspection')
    return {'fingerprint':value['fingerprint'],'keyring_sha256':hashlib.sha256(data).hexdigest(),
            'created_unix':value['created_unix'],'expires_unix':value['expires_unix'],'bytes':data}


def valid_window(issued,expires,trust,*,now=None):
    now=int(time.time()) if now is None else now
    if type(issued) is not int or type(expires) is not int or not 0<expires-issued<=MAX_VALIDITY or issued>now+300 or expires<=now or issued<trust['created_unix'] or expires>trust['expires_unix']:
        raise ValueError('Finite current release validity and certificate lifetime required')



def legal_name(kind,digest):
    if kind not in ('copyright','source_notices_index') or not isinstance(digest,str) or not p.HASH.fullmatch(digest):raise ValueError('Exact legal asset kind/content hash required')
    return ('copyright_' if kind=='copyright' else 'source-notices_')+digest+('.txt' if kind=='copyright' else '.json')


def merge_legal_assets(destination,incoming):
    for name,data in incoming.items():
        match=re.fullmatch(r'(copyright|source-notices)_([a-f0-9]{64})\.(txt|json)',name)
        if match is None or (match[1],match[3]) not in (('copyright','txt'),('source-notices','json')) or not isinstance(data,bytes) or hashlib.sha256(data).hexdigest()!=match[2]:raise ValueError('Legal asset content differs from canonical kind/SHA filename')
        if name in destination and destination[name]!=data:raise ValueError('Conflicting legal asset content identity')
        destination[name]=data


def legal_assets(archive,component):
    selected={row['path']:kind for kind in ('copyright','source_notices_index') if (row:=component.get(kind))}
    result={};names={}
    with p.tar_stream(archive,'--fsys-tarfile') as stream:
        for member in stream:
            virtual='/'+member.name.removeprefix('./').rstrip('/')
            kind=selected.get(virtual)
            if kind is None:continue
            if not member.isfile() or member.size>64*1024**2:raise ValueError('Bounded original public legal file required')
            data=stream.extractfile(member).read();expected=component[kind]['sha256']
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Actual public legal file differs')
            name=legal_name(kind,expected)
            result[name]=data;names[kind]=name
    if set(names)!=set(selected.values()):raise ValueError('Actual public legal assets incomplete')
    return result,names


def collect(projection_paths,additional_path,acquisition_records,records,archives,*,repository=ROOT,target=Path('/mnt/lfs')):
    """Actual archive/control/payload/legal verification, not package acceptance."""
    rows={};inputs={}
    def add(row):
        name=row.get('name')
        if not isinstance(name,str) or not p.NAME.fullmatch(name):raise ValueError('Native component identity')
        if name in rows and rows[name]!=row:raise ValueError('Conflicting selected native package')
        rows[name]=row
    for path in projection_paths:
        path=p.regular(path);document=p.strict(path.read_bytes())
        if document.get('schema_version')!=1 or not isinstance(document.get('components'),list):raise ValueError('Native projection shape')
        if path.name in inputs and inputs[path.name]!=p.digest(path):raise ValueError('Projection basename custody collision')
        inputs[path.name]=p.digest(path)
        for row in document['components']:add(row)
    if additional_path is not None:
        path=p.regular(additional_path);additional=p.strict(path.read_bytes());inputs[path.name]=p.digest(path)
        if not isinstance(additional,list) or {row.get('name') for row in additional}!=p.MANDATORY_ADDITIONS:raise ValueError('Only exact offline mandatory additions')
        for row in additional:add(row)
    optional=set()
    for path in acquisition_records:
        path=p.regular(path);record=p.strict(path.read_bytes());name=record.get('name')
        if name not in PACKAGES or name in optional:raise ValueError('Only one exact curated acquisition record per package')
        optional.add(name);add(p.component_from_record(path,archives))
    if optional and optional!=PACKAGES:raise ValueError('All four curated acquisition native records required')
    verified={}
    for name,row in sorted(rows.items()):
        stem=name+'_'+row['version']+'_'+row['architecture'];record_path=p.regular(Path(records)/(stem+'.json'))
        component=p.component_from_record(record_path,archives)
        if component!=row:raise ValueError('Projection/native record metadata differs')
        record=p.strict(record_path.read_bytes());archive=p.regular(Path(archives)/(stem+'.deb'))
        control,payload,installed_bytes=p.archive_contents(archive)
        if control.get('Pre-Depends'):raise ValueError('Native Pre-Depends ordering remains unqualified')
        if not component['sources']:original_source_provenance(component,record,repository=repository,target=target)
        if not p.HASH.fullmatch(component['recipe_sha256']) or any(not p.HASH.fullmatch(source.get('sha256','')) for source in component['sources']):raise ValueError('Native source/recipe custody')
        if len({key.lower() for key in control})!=len(control) or any(key.lower() in {'filename','size','sha256','md5sum','sha1'} for key in control):raise ValueError('Package control cannot supply repository authority')
        asset=name+'_'+p.digest(archive)+'.deb'
        if not re.fullmatch('[a-z0-9][a-z0-9+.-]*_[a-f0-9]{64}\\.deb',asset):raise ValueError('Flat release asset name')
        legal,legal_names=legal_assets(archive,component)
        verified[name]={'component':component,'control':control,'payload':{virtual:payload[virtual] for virtual,owner in POSTCONDITIONS.items() if owner==name},'installed_bytes':installed_bytes,
            'archive':archive,'record':record_path,'asset':asset,'legal_data':legal,'legal_assets':legal_names}
    if not verified:raise ValueError('Empty native repository')
    return verified,inputs


def render_control(control):
    out=[]
    for key,value in control.items():
        if not re.fullmatch('[A-Za-z][A-Za-z0-9-]*',key) or not isinstance(value,str) or any(c in value for c in '\r\0'):
            raise ValueError('Native package control field')
        lines=value.split('\n');out.append(key+': '+lines[0])
        out.extend(' '+line for line in lines[1:])
    return '\n'.join(out)+'\n\n'


def documents(verified,trust,issued,expires,*,now=None):
    valid_window(issued,expires,trust,now=now);paragraphs=[];inventory=[];legal_files={}
    first=('Package','Version','Architecture','Maintainer','Installed-Size','Depends','Section','Priority','Description')
    for name,item in sorted(verified.items()):
        control=item['control'];fields={key:control[key] for key in first if key in control}
        fields.update({key:control[key] for key in sorted(set(control)-set(first))})
        fields.update(Filename=item['asset'],Size=str(item['archive'].stat().st_size),SHA256=p.digest(item['archive']))
        paragraphs.append(render_control(fields))
        row=item['component'];merge_legal_assets(legal_files,item['legal_data'])
        inventory.append({**row,'asset':item['asset'],'archive_bytes':item['archive'].stat().st_size,
            'installed_bytes':item['installed_bytes'],'legal_assets':item['legal_assets'],
            'postconditions':{virtual:item['payload'][virtual]['sha256'] for virtual,owner in POSTCONDITIONS.items() if owner==name}})
    packages=''.join(paragraphs).encode();compressed=gzip.compress(packages,mtime=0)
    release=('Origin: Toddy OS\nLabel: Toddy OS experimental native\nSuite: experimental\nCodename: toddy-phase2\n'
        +'Date: '+format_datetime(datetime.fromtimestamp(issued,timezone.utc),usegmt=True)+'\n'
        +'Valid-Until: '+format_datetime(datetime.fromtimestamp(expires,timezone.utc),usegmt=True)+'\n'
        +'Architectures: amd64 all\nDescription: Exact experimental Toddy native archives; no runtime acceptance inferred\nAcquire-By-Hash: no\nSHA256:\n'
        +' '+hashlib.sha256(packages).hexdigest()+' '+str(len(packages))+' Packages\n'
        +' '+hashlib.sha256(compressed).hexdigest()+' '+str(len(compressed))+' Packages.gz\n').encode()
    native_trust={'version':1,'fingerprint':trust['fingerprint'],'keyring_sha256':trust['keyring_sha256']}
    return {'Packages':packages,'Packages.gz':compressed,'Release':release,'archive-keyring.gpg':trust['bytes'],
        'native-trust.json':p.encoded(native_trust),**legal_files},inventory


def reserve_for(output,scope):
    output=Path(output)
    if scope=='host-export':return HOST_RESERVE
    if scope!='native-target':raise ValueError('Explicit artifact capacity scope required')
    root=Path('/mnt/lfs') if output.is_relative_to('/mnt/lfs/sources/stage') else Path('/')
    if not output.is_relative_to(root/'sources/stage'):raise ValueError('Native export must remain designated stage')
    node=Path('/dev/vdb4').stat()
    if not stat.S_ISBLK(node.st_mode) or root.stat().st_dev!=node.st_rdev:raise ValueError('Native export target identity')
    serial=subprocess.check_output(['/usr/bin/lsblk','-dn','-o','SERIAL','/dev/vdb'],text=True,timeout=5).strip()
    if serial!='TODDY-LFS-TARGET':raise ValueError('Native export target serial')
    return NATIVE_RESERVE


def export(output,verified,inputs,trust,issued,expires,*,scope='host-export',now=None):
    output=Path(output)
    if not output.is_absolute() or output.resolve()!=output or os.path.lexists(output) or not output.parent.is_dir():raise ValueError('New canonical unsigned export required')
    files,inventory=documents(verified,trust,issued,expires,now=now)
    archive_bytes=sum(row['archive'].stat().st_size for row in verified.values())
    expected_hashes={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
    expected_hashes.update({item['asset']:item['component']['archive_sha256'] for item in verified.values()})
    receipt={'version':1,'kind':'unsigned-flat-native-archive-export','issued_unix':issued,'expires_unix':expires,
        'public_fingerprint':trust['fingerprint'],'public_keyring_sha256':trust['keyring_sha256'],'inputs':inputs,
        'packages':inventory,'files':expected_hashes,'producer_sha256':p.digest(__file__),
        'signed':False,'published':False,'qualification_created':False,'native_repository_qualified':False}
    receipt_bytes=p.encoded(receipt);reserve=reserve_for(output,scope)
    headroom=4096*(len(expected_hashes)+2)
    if shutil.disk_usage(output.parent).free<reserve+archive_bytes+sum(map(len,files.values()))+len(receipt_bytes)+headroom:raise ValueError('Artifact export capacity reserve')
    output.mkdir(mode=0o700);hashes={}
    # No overwrite/resume: a partial directory is preserved after interruption.
    for name,data in files.items():
        with (output/name).open('xb') as stream:os.fchmod(stream.fileno(),0o644);stream.write(data);stream.flush();os.fsync(stream.fileno())
        hashes[name]=p.digest(output/name)
    for item in verified.values():
        destination=output/item['asset']
        with item['archive'].open('rb') as source,destination.open('xb') as stream:
            os.fchmod(stream.fileno(),0o644);shutil.copyfileobj(source,stream,1024**2);stream.flush();os.fsync(stream.fileno())
        if p.digest(destination)!=item['component']['archive_sha256'] or p.digest(item['record'])!=item['component']['component_record_sha256']:raise ValueError('Native inputs changed during export')
        hashes[item['asset']]=p.digest(destination)
    if hashes!=expected_hashes or shutil.disk_usage(output).free<reserve+len(receipt_bytes)+4096:raise ValueError('Export verification/capacity changed before completion')
    with (output/'archive-export.json').open('xb') as stream:os.fchmod(stream.fileno(),0o644);stream.write(receipt_bytes);stream.flush();os.fsync(stream.fileno())
    descriptor=os.open(output,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--projection',type=Path,action='append',required=True)
    parser.add_argument('--additional-components',type=Path)
    parser.add_argument('--acquisition-record',type=Path,action='append',default=[])
    parser.add_argument('--records',type=Path,default=Path('/var/log/toddy/packages'))
    parser.add_argument('--archives',type=Path,default=Path('/var/cache/toddy/packages'))
    parser.add_argument('--target-root',type=Path,default=Path('/mnt/lfs'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--issued-unix',type=int,required=True);parser.add_argument('--expires-unix',type=int,required=True)
    parser.add_argument('--capacity-scope',choices=('host-export','native-target'),required=True)
    args=parser.parse_args();trust=public_trust()
    verified,inputs=collect(args.projection,args.additional_components,args.acquisition_record,args.records,args.archives,target=args.target_root)
    result=export(args.output,verified,inputs,trust,args.issued_unix,args.expires_unix,scope=args.capacity_scope)
    print(p.encoded({'state':result['kind'],'packages':len(result['packages']),'signed':False,'published':False}).decode(),end='')


if __name__=='__main__':main()
