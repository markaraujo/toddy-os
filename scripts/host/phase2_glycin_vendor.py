#!/usr/bin/env python3
"""Freeze Glycin Cargo closure, reusing checked compressed registry cache; no host build."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import tomllib

ROOT=Path(__file__).resolve().parents[2]
REGISTRY='registry+https://github.com/rust-lang/crates.io-index'


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def registry_packages(body):
    packages=[]
    for row in tomllib.loads(body.decode())['package']:
        if 'source' not in row:continue
        if row['source']!=REGISTRY:
            raise ValueError('Only the explicit official public registry is allowed')
        name,version,sha=row['name'],row['version'],row.get('checksum','')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}',name):raise ValueError('Unsafe crate name')
        if not re.fullmatch(r'[0-9][A-Za-z0-9.+-]{0,95}',version):raise ValueError('Unsafe crate version')
        if not re.fullmatch(r'[a-f0-9]{64}',sha):raise ValueError('Missing/invalid crate checksum')
        packages.append({'name':name,'version':version,'sha256':sha})
    if not packages:raise ValueError('Empty registry closure')
    if len({(p['name'],p['version']) for p in packages})!=len(packages):raise ValueError('Ambiguous crate identity')
    return sorted(packages,key=lambda p:(p['name'],p['version']))


def verify_vendor(vendor,packages):
    assert vendor.is_dir() and not vendor.is_symlink()
    assert {p.name for p in vendor.iterdir()}=={p['name']+'-'+p['version'] for p in packages}
    result=[]
    for package in packages:
        directory=vendor/(package['name']+'-'+package['version'])
        assert directory.resolve().is_relative_to(vendor.resolve()) and not directory.is_symlink()
        checksum_file=directory/'.cargo-checksum.json'
        assert checksum_file.is_file() and not checksum_file.is_symlink()
        checksum=json.loads(checksum_file.read_text())
        assert checksum['package']==package['sha256']
        actual={}
        for path in directory.rglob('*'):
            assert not path.is_symlink(), 'Unexpected source symlink needs review'
            if path.is_file() and path!=checksum_file:
                actual[str(path.relative_to(directory))]=digest(path)
        assert actual==checksum['files'],package['name']+' source content drift'
        metadata=tomllib.loads((directory/'Cargo.toml').read_text())['package']
        assert metadata['name']==package['name'] and metadata['version']==package['version']
        result.append({**package,'files':len(actual),'file_manifest_sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                       'license':metadata.get('license'),'license_file':metadata.get('license-file')})
    return result


def bundle(vendor,destination):
    assert not destination.exists() and not destination.with_suffix(destination.suffix+'.part').exists()
    part=destination.with_suffix(destination.suffix+'.part')
    with part.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=1780340400) as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.PAX_FORMAT) as archive:
            for path in [vendor,*sorted(vendor.rglob('*'))]:
                assert not path.is_symlink()
                info=archive.gettarinfo(str(path),arcname='vendor'+('/'+str(path.relative_to(vendor)) if path!=vendor else ''))
                info.uid=info.gid=0;info.uname=info.gname='';info.mtime=1780340400
                if path.is_file():
                    with path.open('rb') as source:archive.addfile(info,source)
                else:archive.addfile(info)
    part.replace(destination)
    return {'filename':destination.name,'sha256':digest(destination),'bytes':destination.stat().st_size}


def main():
    assert shutil.disk_usage(ROOT).free>=100*1024**3
    context=ROOT/'.local/phase2/glycin-vendor-1'
    assert not context.exists(),'Inspect actual source job/cache/postconditions before any continuation'
    sources_path=ROOT/'config/phase2/sources.lock.json'
    sources=json.loads(sources_path.read_text());rows={r['name']:r for r in sources['components']}
    tool_root=ROOT/'.local/phase2/cargo-prefetch-tools-1'
    tools=json.loads((tool_root/'proof.json').read_text())
    for row in tools['archives']:assert digest(ROOT/'.local/sources'/row['filename'])==row['sha256']
    executables={}
    for name in ['cargo','rustc']:
        record=tools['versions'][name];path=ROOT/record['path']
        assert digest(path)==record['binary_sha256'];executables[name]=str(path)
        assert subprocess.check_output([str(path),'--version'],text=True).strip()==record['stdout']
    parents=[]
    for name in ['glycin']:
        row=rows[name];path=ROOT/'.local/sources'/row['filename'];assert digest(path)==row['sha256']
        with tarfile.open(path) as archive:
            roots={m.name.split('/')[0] for m in archive.getmembers()};assert len(roots)==1
            source_root=roots.pop();lock_name=source_root+'/Cargo.lock'
            body=archive.extractfile(lock_name).read()
        parents.append({'name':name,'version':row['version'],'archive':row['filename'],'source_sha256':row['sha256'],
                        'source_root':source_root,'lock':body,'packages':registry_packages(body)})
    identities={}
    for parent in parents:
        for row in parent['packages']:
            key=(row['name'],row['version']);assert identities.get(key,row['sha256'])==row['sha256'];identities[key]=row['sha256']
    context.mkdir();(context/'home').mkdir();(context/'source').mkdir()
    job={'pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
         'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time(),
         'script_sha256':digest(Path(__file__)),'scope':'Source acquisition/vendor checksum verification only; native product compilation remains guest Rust1.97.1',
         'tools':tools,'parents':[{k:v for k,v in p.items() if k not in ['lock','packages']} for p in parents]}
    (context/'job.json').write_text(json.dumps(job,indent=2)+'\n')
    wrapper=context/'metadata-only-rustc.py'
    wrapper.write_text('''#!/usr/bin/python3
import json,os,subprocess,sys
from pathlib import Path
args=sys.argv[2:]
allowed=args in [['-vV'],['-V'],['--version']] or (any(a.startswith('--print') for a in args) and not any(a=='-o' or a.startswith('--emit') or a.startswith('--out-dir') or a.endswith('.rs') for a in args))
with Path(__file__).with_suffix('.jsonl').open('a') as out:out.write(json.dumps({'metadata_only':allowed,'args':args})+'\\n')
if not allowed:raise SystemExit(86)
raise SystemExit(subprocess.run(sys.argv[1:]).returncode)
''');wrapper.chmod(0o755)
    env={'PATH':'/usr/bin:/bin','HOME':str(context/'home'),'CARGO_HOME':str(ROOT/'.local/phase2/rust-vendor-1/home'),
         'RUSTC':executables['rustc'],'RUSTC_WRAPPER':str(wrapper),'CARGO_NET_RETRY':'1',
         'CARGO_REGISTRIES_CRATES_IO_PROTOCOL':'sparse','CARGO_TERM_COLOR':'never'}
    for key in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR']:
        if key in os.environ:env[key]=os.environ[key]
    result=[];exit_code=1
    try:
        for parent in parents:
            name=parent['name'];directory=context/name;directory.mkdir()
            with tarfile.open(ROOT/'.local/sources'/parent['archive']) as archive:
                archive.extractall(context/'source',filter='data')
            source=context/'source'/parent['source_root'];lock=source/'Cargo.lock'
            assert lock.read_bytes()==parent['lock']
            assert not any((source/'.cargo'/n).exists() for n in ['config','config.toml'])
            command=[executables['cargo'],'vendor','--locked','--versioned-dirs','--manifest-path',str(source/'Cargo.toml'),str(directory/'vendor')]
            with tempfile.TemporaryDirectory(prefix='toddy-source-vendor-') as cwd:
                assert not any((p/'.cargo'/n).exists() for p in [Path(cwd),*Path(cwd).parents] for n in ['config','config.toml'])
                with (directory/'cargo-vendor.log').open('xb') as output:
                    completed=subprocess.run(command,cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT)
            (directory/'cargo-vendor.exit').write_text(str(completed.returncode)+'\n')
            assert completed.returncode==0,name+' source acquisition failed; preserve cache and actual log'
            assert lock.read_bytes()==parent['lock']
            assert shutil.disk_usage(ROOT).free>=100*1024**3
            packages=verify_vendor(directory/'vendor',parent['packages'])
            artifact=bundle(directory/'vendor',ROOT/'.local/sources'/(name+'-'+parent['version']+'-vendor.tar.gz'))
            record={'name':name,'version':parent['version'],'primary_archive':parent['archive'],'primary_source_sha256':parent['source_sha256'],
                    'cargo_lock_sha256':hashlib.sha256(parent['lock']).hexdigest(),'vendor_exit':0,'artifact':artifact,'packages':packages}
            (directory/'verified.json').write_text(json.dumps(record,indent=2)+'\n');result.append(record)
            print(json.dumps({'parent':name,'registry_crates':len(packages),'artifact':artifact,'vendor_exit':0}),flush=True)
        if wrapper.with_suffix('.jsonl').exists():
            requests=[json.loads(l) for l in wrapper.with_suffix('.jsonl').read_text().splitlines()]
            assert all(r['metadata_only'] for r in requests)
        else:requests=[]
        manifest={'scope':'Authenticated native-build dependency sources, not native compilation/install/GUI acceptance',
                  'tool_versions':tools['versions'],'host_source_compilations':0,'metadata_requests':len(requests),
                  'registry':REGISTRY,'parents':result}
        contract=ROOT/'config/phase2/glycin-crates.lock.json';assert not contract.exists()
        contract.write_text(json.dumps(manifest,indent=2)+'\n')
        current=json.loads(sources_path.read_text());assert current==sources,'Reconcile concurrent source-lock mutation'
        for parent in result:
            name=parent['name']+'-vendor';assert not any(r['name']==name for r in current['components'])
            current['components'].append({'name':name,'version':parent['version'],**parent['artifact'],
                'url':'generated:phase2_glycin_vendor/'+name,'reference':'Derived Cargo vendor from authenticated primary/published lock; all registry package/file checksums verified',
                'parent_source_sha256':parent['primary_source_sha256'],'cargo_lock_sha256':parent['cargo_lock_sha256'],
                'producer_sha256':job['script_sha256'],'registry_crates':len(parent['packages']),'integrity':'Official Cargo vendor plus independent exact package/file-manifest verification before archive freezing','status':'source_verified'})
        sources_path.write_text(json.dumps(current,indent=2)+'\n')
        (context/'verified.json').write_text(json.dumps(manifest,indent=2)+'\n');exit_code=0
    finally:(context/'exit').write_text(str(exit_code)+'\n')


if __name__=='__main__':main()
