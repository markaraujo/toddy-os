#!/usr/bin/python3 -I
"""Deterministic selected corresponding-source assets; no download or signing."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(HERE)]
import offline_payload as p
import archive_metadata as metadata
import acquisition_declarations as declarations
import voice_catalog_sources as generated_voice

MAX_ASSET=1_900_000_000
PROJECT_ALLOW=('AGENTS.md','PRD.md','README.md','LICENSE','LICENSES','Makefile','config','runtime','scripts','stories','docs','tests','dashboard','ui','assets','.github')
FOUNDATION_SHA='f06ae9910e4f38338f35e472e71c92f0031a1b40c4762c30583e3688d4d30911'
FOUNDATION_URL='https://github.com/markaraujo/toddy-os/releases/download/v0.1.0-foundation.1/source-archives.tar'


def git(repository,*args):return subprocess.check_output(['git',*args],cwd=repository,stderr=subprocess.PIPE)


def relative(value):
    p.canonical(value,absolute=False)
    if value.split('/')[0] not in PROJECT_ALLOW or any(part in ('.git','.local','.gnupg','node_modules','__pycache__') or part.startswith('.env') for part in Path(value).parts):raise ValueError('Reviewed tracked project source path required: '+value)
    return value


def regular(path):
    path=p.regular(Path(path))
    if path.resolve()!=path:raise ValueError('Canonical source custody path required')
    return path


def hash_stream(stream,algorithm='sha256'):
    digest=hashlib.new(algorithm);size=0
    while data:=stream.read(1024*1024):digest.update(data);size+=len(data)
    return digest.hexdigest(),size


class Input:
    def __init__(self,name,sha256,*,path=None,data=None,foundation=None,member=None,origin=None):
        p.canonical(name,absolute=False)
        if not p.HASH.fullmatch(sha256):raise ValueError('Exact selected source SHA256 required')
        self.name=name;self.sha256=sha256;self.path=path;self.data=data;self.foundation=foundation;self.member=member;self.origin=origin
        with self.open() as stream:actual,self.size=hash_stream(stream)
        if actual!=sha256:raise ValueError('Selected source bytes differ: '+name)
        if self.size+4096>MAX_ASSET:raise ValueError('Single selected input exceeds supported public tar asset size: '+name)
    @contextmanager
    def open(self):
        if self.path is not None:
            with regular(self.path).open('rb') as stream:yield stream
        elif self.data is not None:
            with io.BytesIO(self.data) as stream:yield stream
        else:
            with tarfile.open(self.foundation,'r:') as archive:
                stream=archive.extractfile(self.member)
                if stream is None:raise ValueError('Selected foundation source is not regular')
                with stream:yield stream
    def description(self):return {'path':self.name,'sha256':self.sha256,'bytes':self.size,'origin':self.origin}


class Resolver:
    def __init__(self,roots,foundation=None):
        self.roots=[Path(root) for root in roots];self.foundation=None;self.members={}
        for root in self.roots:
            if root.resolve()!=root or not root.is_dir():raise ValueError('Canonical explicit source root required')
        if foundation:
            self.foundation=regular(foundation)
            if p.digest(self.foundation)!=FOUNDATION_SHA:raise ValueError('Published foundation source asset differs')
            with tarfile.open(self.foundation,'r:') as archive:
                for member in archive:
                    if member.isfile():self.members.setdefault(Path(member.name).name,[]).append(member.name)
    def source(self,filename,sha):
        if not isinstance(filename,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]{0,220}',filename):raise ValueError('Explicit flat selected source filename required')
        for root in self.roots:
            path=root/filename
            if os.path.lexists(path) and p.digest(regular(path))==sha:return Input('upstream/'+sha+'/'+filename,sha,path=path,origin={'kind':'selected-native-source','filename':filename})
        for member in self.members.get(filename,[]):
            try:return Input('upstream/'+sha+'/'+filename,sha,foundation=self.foundation,member=member,origin={'kind':'published-foundation-member','url':FOUNDATION_URL,'asset_sha256':FOUNDATION_SHA,'member':member})
            except ValueError:continue
        raise ValueError('Missing exact selected source archive: '+filename+' '+sha)


class Project:
    def __init__(self,repository,commit):
        self.repository=Path(repository);self.commit=commit;self.blobs={};self.cache={}
        if not re.fullmatch('[a-f0-9]{40}',commit) or git(self.repository,'rev-parse',commit+'^{commit}').decode().strip()!=commit:raise ValueError('Actual explicit project Git commit required')
        self.paths=[];self.bytes=0
        for row in git(self.repository,'ls-tree','-rlz',commit).split(b'\0'):
            if not row:continue
            header,path=row.split(b'\t',1);mode,kind,oid,size=header.decode().split();path=path.decode('utf-8',errors='strict')
            if path.split('/')[0] not in PROJECT_ALLOW:continue
            relative(path)
            if kind!='blob' or mode not in ('100644','100755','120000'):raise ValueError('No submodule/foreign project source')
            self.paths.append(path);self.bytes+=int(size)+2048
        if not self.paths:raise ValueError('Reviewed Git source snapshot empty')
    def source(self,path,expected):
        relative(path);key=(path,expected)
        if key in self.cache:return self.cache[key]
        if not p.HASH.fullmatch(expected):raise ValueError('Project input hash required')
        candidates=[self.commit]+git(self.repository,'log',self.commit,'--format=%H','--',path).decode().splitlines()
        for commit in dict.fromkeys(candidates):
            try:data=git(self.repository,'show',commit+':'+path)
            except subprocess.CalledProcessError:continue
            if hashlib.sha256(data).hexdigest()!=expected:continue
            result=Input('project-inputs/'+expected+'/'+path,expected,data=data,origin={'kind':'committed-exact-project-input','commit':commit,'path':path})
            self.cache[key]=result;return result
        raise ValueError('Missing exact committed historical project input: '+path+' '+expected)
    def snapshot(self,output):
        selected=sorted({path.split('/')[0] for path in self.paths})
        with output.open('xb') as stream:
            process=subprocess.run(['git','archive','--format=tar','--prefix=toddy-project/',self.commit,'--',*selected],cwd=self.repository,stdout=stream,stderr=subprocess.PIPE)
            if process.returncode:raise ValueError('Exact tagged project source archive failed')
            stream.flush();os.fsync(stream.fileno())
        if output.stat().st_size>MAX_ASSET:raise ValueError('Project snapshot exceeds public asset size')


def package_documents(archive,name,body):
    prefix='/usr/share/doc/'+name+'/';result={}
    with p.tar_stream(archive,'--fsys-tarfile') as stream:
        for member in stream:
            path='/'+member.name.removeprefix('./').rstrip('/')
            if not member.isfile():continue
            if name == generated_voice.bridge.PACKAGE and path == generated_voice.CATALOG:
                local='catalog.json'
            elif path.startswith(prefix):local=path[len(prefix):]
            else:continue
            generated = name == generated_voice.bridge.PACKAGE and local in generated_voice.DOCUMENTS | {'catalog.json'}
            if not generated and local not in ('source-manifest.json','npm-custody.json','supplemental-notices.json','copyright') and not local.startswith(('source-notices/','npm-supplemental-notices/')):continue
            if member.size>32*1024**2:raise ValueError('Bounded original source/notice document required')
            data=stream.extractfile(member).read()
            if hashlib.sha256(data).hexdigest()!=body.get(path,{}).get('sha256'):raise ValueError('Original source document ownership differs')
            result[local]=data
    return result


def collect(repository,receipt,records,resolver,project,npm_cache,generated_catalog_attestation=None,generated_catalog_projection=None):
    entries={};coverage=[]
    generated_present = any(row.get('name') == generated_voice.bridge.PACKAGE for row in receipt['packages'])
    if generated_present != (generated_catalog_attestation is not None and generated_catalog_projection is not None) or (not generated_present and (generated_catalog_attestation is not None or generated_catalog_projection is not None)):
        raise ValueError('Exact generated catalog requires explicit builder attestation and projection')
    export_documents={}
    if generated_present:
        for key,path in (('attestation',generated_catalog_attestation),('projection',generated_catalog_projection)):
            path=regular(path)
            if path.stat().st_size > 4*1024**2:raise ValueError('Bounded actual generated export proof required')
            export_documents[key]=path.read_bytes()
        attestation=p.strict(export_documents['attestation']);projection=p.strict(export_documents['projection'])
        if (receipt.get('inputs',{}).get('optional-projection.json') != hashlib.sha256(export_documents['projection']).hexdigest() or
                projection.get('generated_catalog_attestation_sha256') != hashlib.sha256(export_documents['attestation']).hexdigest()):
            raise ValueError('Actual archive export/projection/attestation digest chain differs')
    def add(item):
        if item.name in entries and entries[item.name].description()!=item.description():raise ValueError('Conflicting corresponding-source identity')
        entries[item.name]=item;return item.name
    for component in receipt['packages']:
        name=component['name'];stem=name+'_'+component['version']+'_'+component['architecture']
        path=regular(Path(records)/(stem+'.json'));raw=p.strict(path.read_bytes())
        archive=regular(Path(repository)/component['asset']);control,body,_=p.archive_contents(archive)
        if p.digest(path)!=component['component_record_sha256'] or raw.get('installed') is not True or raw.get('payload')!=body or raw.get('archive_sha256')!=p.digest(archive) or (raw.get('name'),raw.get('version'),control.get('Architecture'))!=(name,component['version'],component['architecture']) or (control.get('Package'),control.get('Version'))!=(name,component['version']):raise ValueError('Actual native source record/archive custody differs')
        if [{('public_verification_material_sha256' if key=='key_sha256' else key):value for key,value in source.items()} for source in raw['sources']]!=component['sources']:raise ValueError('Native declared source rows differ from actual record')
        selected=[]
        for source in component['sources']:selected.append(add(resolver.source(source.get('filename'),source['sha256'])))
        supporting=raw.get('supporting_build_scripts',{});files=supporting.get('files',{})
        if not files or hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=supporting.get('sha256') or raw['recipe_sha256'] not in files.values() or raw['packager_sha256'] not in files.values():raise ValueError('Exact native build recipe closure missing')
        for relative_path,digest in sorted(files.items()):selected.append(add(project.source('scripts/build/'+relative_path,digest)))
        documents=package_documents(archive,name,body)
        for local,data in documents.items():selected.append(add(Input('package-documents/'+name+'/'+local,hashlib.sha256(data).hexdigest(),data=data,origin={'kind':'archive-owned-original-document','archive_sha256':component['archive_sha256']})))
        if name == generated_voice.bridge.PACKAGE:
            inputs=generated_voice.verify(component,raw,documents,attestation,projection)
            for relative_path,digest in sorted(inputs.items()):selected.append(add(project.source(relative_path,digest)))
            attribution=p.strict(documents['human-sample-attribution.json'])
            if set(attribution.get('samples',{})) != {'en','pt-BR'}:raise ValueError('Exact attributed human source samples required')
            for locale,row in attribution['samples'].items():
                selected.append(add(project.source('tests/fixtures/voice/human/'+locale+'.wav',row['wav']['sha256'])))
            for role,data in export_documents.items():
                selected.append(add(Input('builder-export/voice-native2-'+role+'.json',hashlib.sha256(data).hexdigest(),data=data,origin={'kind':'actual-builder-export-proof-retained-for-owner-signed-source-review'})))
        elif not component['sources']:
            with tempfile.TemporaryDirectory(prefix='toddy-public-original-source-') as directory:
                target=Path(directory)
                if 'source-manifest.json' in documents:
                    owned=target/'usr/share/doc'/name/'source-manifest.json';owned.parent.mkdir(parents=True);owned.write_bytes(documents['source-manifest.json'])
                provenance=metadata.original_source_provenance(component,raw,target=target,repository=project.repository)
            if 'source-manifest.json' in documents:
                manifest=p.strict(documents['source-manifest.json']);inputs=manifest.get('source_inputs',manifest.get('inputs'))
                if manifest.get('package')!=name or not isinstance(inputs,dict) or not inputs:raise ValueError('Original project source manifest missing')
                for relative_path,value in sorted(inputs.items()):selected.append(add(project.source(relative_path,value['sha256'] if isinstance(value,dict) else value)))
            elif provenance!='committed-original-record':raise ValueError('No foreign empty-source fallback')
        if name=='toddy-agent':
            custody=p.strict(documents.get('npm-custody.json',b'{}'));rows=custody.get('components',[]);archives=set()
            if len(rows)!=88 or custody.get('distinct_archives')!=87 or npm_cache is None:raise ValueError('Actual complete audited npm archive closure required')
            for notice in p.strict(documents.get('supplemental-notices.json',b'[]')):
                if hashlib.sha256(documents.get('npm-supplemental-notices/'+notice['sha256'],b'')).hexdigest()!=notice['sha256']:raise ValueError('Actual audited supplemental notice missing')
            for row in rows:
                if row.get('lifecycle_scripts_executed') is not False:raise ValueError('Audited npm provenance required')
                algorithm,encoded=row['integrity'].split('-',1);sha512=base64.b64decode(encoded,validate=True)
                path=regular(Path(npm_cache)/('npm-'+sha512.hex()+'.tgz'))
                if algorithm!='sha512' or len(sha512)!=64 or path.stat().st_size!=row['archive_bytes']:
                    raise ValueError('Actual audited npm archive size/integrity differs')
                with path.open('rb') as source:
                    if hash_stream(source,'sha512')[0]!=sha512.hex():raise ValueError('Actual audited npm SHA512 differs')
                selected.append(add(Input('npm/'+row['archive_sha256']+'.tgz',row['archive_sha256'],path=path,origin={'kind':'audited-npm-source-archive','url':row['url'],'integrity':row['integrity']})));archives.add(row['archive_sha256'])
            if len(archives)!=87:raise ValueError('Complete distinct npm source custody required')
        coverage.append({'name':name,'version':component['version'],'architecture':component['architecture'],'archive_sha256':component['archive_sha256'],'component_record_sha256':component['component_record_sha256'],'recipe_sha256':component['recipe_sha256'],'source_members':sorted(set(selected))})
    return entries,coverage


def bundles(entries,output,prefix='selected-sources'):
    result=[];current=None;used=10240;number=0
    def finish():
        nonlocal current
        if current:
            current.close()
            with path.open('rb') as stream:os.fsync(stream.fileno())
            if path.stat().st_size>MAX_ASSET:raise ValueError('Public source asset bound exceeded')
            result.append({'name':path.name,'sha256':p.digest(path),'bytes':path.stat().st_size});current=None
    try:
        for name,item in sorted(entries.items()):
            # PAX long-name headers and tar end padding are included conservatively.
            needed=((item.size+511)//512)*512+4096
            if current is not None and used+needed>MAX_ASSET:finish();used=10240
            if current is None:
                number+=1;path=output/(prefix+'-'+str(number).zfill(3)+'.tar');current=tarfile.open(path,'x',format=tarfile.PAX_FORMAT)
            info=tarfile.TarInfo(name);info.size=item.size;info.mode=0o644;info.uid=info.gid=0;info.mtime=0;info.uname=info.gname=''
            with item.open() as stream:
                class Observed:
                    def __init__(self):self.sha=hashlib.sha256();self.size=0
                    def read(self,size=-1):
                        data=stream.read(size);self.sha.update(data);self.size+=len(data);return data
                observed=Observed();current.addfile(info,observed)
                if (observed.sha.hexdigest(),observed.size)!=(item.sha256,item.size):raise ValueError('Selected source changed during public tar copy')
            used+=needed
        finish();return result
    finally:
        if current is not None:current.close()


def export(repository,records,source_roots,commit,output,scope,npm_cache=None,foundation=None,generated_catalog_attestation=None,generated_catalog_projection=None):
    receipt,_index=declarations.verified_repository(repository,metadata.public_trust())
    project=Project(ROOT,commit);resolver=Resolver(source_roots,foundation)
    entries,coverage=collect(repository,receipt,records,resolver,project,npm_cache,generated_catalog_attestation,generated_catalog_projection)
    output=Path(output)
    if not output.is_absolute() or output.resolve()!=output or os.path.lexists(output) or not output.parent.is_dir():raise ValueError('Fresh canonical corresponding-source output required')
    licenses={name:item for name,item in entries.items() if name.startswith('package-documents/') and (name.endswith('/copyright') or '/source-notices/' in name or '/npm-supplemental-notices/' in name)}
    reserve=metadata.reserve_for(output,scope);needed=project.bytes+sum(item.size+4096 for item in entries.values())+sum(item.size+4096 for item in licenses.values())+64*1024**2
    if shutil.disk_usage(output.parent).free<reserve+needed:raise ValueError('Corresponding-source capacity reserve')
    output.mkdir(mode=0o700);project_path=output/'toddy-project-source.tar';project.snapshot(project_path)
    source_assets=bundles(entries,output);license_assets=bundles(licenses,output,'source-licenses')
    inventory={'version':1,'kind':'native-package-corresponding-sources','source_commit':commit,
        'archive_export_sha256':p.digest(Path(repository)/'archive-export.json'),'packages':coverage,
        'members':[item.description() for _,item in sorted(entries.items())],'source_assets':source_assets,'license_assets':license_assets,'producer_sha256':p.digest(__file__),
        'project_source':{'name':project_path.name,'sha256':p.digest(project_path),'bytes':project_path.stat().st_size},
        'source_urls_are_additional_only':True,'private_cache_copied':False,'signed':False,'published':False}
    with (output/'source-inventory.json').open('xb') as stream:stream.write(p.encoded(inventory));stream.flush();os.fsync(stream.fileno())
    fd=os.open(output,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return inventory


def verify_assets(inventory_path,artifacts,pins,commit):
    """Independent publication readback: every selected source member is present."""
    inventory=p.strict(regular(inventory_path).read_bytes())
    if type(inventory.get('version')) is not int or inventory['version']!=1 or inventory.get('signed') is not False or inventory.get('published') is not False or inventory.get('kind')!='native-package-corresponding-sources' or inventory.get('producer_sha256')!=p.digest(__file__) or inventory.get('source_commit')!=commit or inventory.get('archive_export_sha256')!=pins['archive_export_sha256'] or inventory.get('source_urls_are_additional_only') is not True or inventory.get('private_cache_copied') is not False:raise ValueError('Actual selected corresponding-source inventory required')
    by_name={row['name']:row for row in artifacts}
    for role,expected in (('source',inventory['source_assets']),('licenses',inventory['license_assets']),('project-source',[inventory['project_source']])):
        if [{key:row[key] for key in ('name','sha256','bytes')} for row in artifacts if row['role']==role]!=expected:raise ValueError('Public source assets differ from complete inventory')
    wanted={row['path']:row for row in inventory['members']}
    if len(wanted)!=len(inventory['members']) or not wanted:raise ValueError('Unique complete source member inventory required')
    package_rows=[]
    for package in inventory['packages']:
        if not package['source_members'] or len(set(package['source_members']))!=len(package['source_members']) or not set(package['source_members'])<=set(wanted):raise ValueError('Missing package corresponding-source coverage')
        package_rows.append({key:package[key] for key in ('name','version','architecture','archive_sha256','component_record_sha256','recipe_sha256')})
    if package_rows!=pins['packages'] or set().union(*(set(row['source_members']) for row in inventory['packages']))!=set(wanted):raise ValueError('Every exact native package and source input must be covered')
    for field,expected in (('source_assets',wanted),('license_assets',{name:row for name,row in wanted.items() if name.startswith('package-documents/') and (name.endswith('/copyright') or '/source-notices/' in name or '/npm-supplemental-notices/' in name)})):
        seen=set()
        for asset in inventory[field]:
            path=regular(by_name[asset['name']]['path'])
            if p.digest(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes'] or path.stat().st_size>MAX_ASSET:raise ValueError('Actual public source tar asset differs')
            with tarfile.open(path,'r:') as archive:
                for member in archive:
                    p.canonical(member.name,absolute=False)
                    if member.name in seen or member.name not in expected or not member.isfile() or (member.uid,member.gid,member.mode,member.mtime)!=(0,0,0o644,0):raise ValueError('Public source tar has extra/unsafe member')
                    with archive.extractfile(member) as stream:actual=hash_stream(stream)
                    if actual!=(expected[member.name]['sha256'],expected[member.name]['bytes']):raise ValueError('Public source tar member changed')
                    seen.add(member.name)
        if seen!=set(expected):raise ValueError('Incomplete public source tar contents')
    project=Project(ROOT,commit);asset=inventory['project_source'];path=regular(by_name[asset['name']]['path'])
    if p.digest(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes'] or path.stat().st_size>MAX_ASSET:raise ValueError('Exact public project snapshot differs')
    seen=set()
    with tarfile.open(path,'r:') as archive:
        if archive.pax_headers.get('comment')!=commit:raise ValueError('Actual tagged Git project archive required')
        for member in archive:
            if member.isdir():continue
            if not member.name.startswith('toddy-project/'):raise ValueError('Public project archive prefix differs')
            name=relative(member.name[len('toddy-project/'):])
            if name in seen or name not in project.paths:raise ValueError('Public project archive contains foreign input')
            original=git(ROOT,'show',commit+':'+name)
            if member.issym():actual=member.linkname.encode()
            elif member.isfile():actual=archive.extractfile(member).read()
            else:raise ValueError('Public project source special entry refused')
            if actual!=original:raise ValueError('Public project source differs from exact tagged commit')
            seen.add(name)
    if seen!=set(project.paths):raise ValueError('Incomplete exact tagged project source snapshot')
    return inventory


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--repository',type=Path,required=True);parser.add_argument('--records',type=Path,required=True)
    parser.add_argument('--source-root',type=Path,action='append',default=[]);parser.add_argument('--source-commit',required=True)
    parser.add_argument('--npm-cache',type=Path);parser.add_argument('--foundation-source-tar',type=Path)
    parser.add_argument('--generated-catalog-attestation',type=Path);parser.add_argument('--generated-catalog-projection',type=Path)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--capacity-scope',choices=('host-export','native-target'),required=True)
    args=parser.parse_args();value=export(args.repository,args.records,args.source_root,args.source_commit,args.output,args.capacity_scope,args.npm_cache,args.foundation_source_tar,args.generated_catalog_attestation,args.generated_catalog_projection)
    print(p.encoded({'state':'unsigned-selected-corresponding-source-assets','source_assets':len(value['source_assets']),'packages':len(value['packages']),'signed':False,'published':False}).decode(),end='')


if __name__=='__main__':main()
