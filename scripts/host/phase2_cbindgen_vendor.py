#!/usr/bin/env python3
"""Freeze exact registry archives directly from the pinned lock; no host compiler."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

from phase2_rust_vendor import ROOT,registry_packages,verify_vendor,bundle,digest


def main():
    assert shutil.disk_usage(ROOT).free>=100*1024**3+128*1024**2
    path=ROOT/'config/phase2/sources.lock.json';lock=json.loads(path.read_text())
    parent=next(r for r in lock['components'] if r['name']=='cbindgen');assert parent['version']=='0.29.4'
    archive=ROOT/'.local/sources'/parent['filename'];assert digest(archive)==parent['sha256']
    with tarfile.open(archive) as t:body=t.extractfile('cbindgen-0.29.4/Cargo.lock').read()
    packages=registry_packages(body);assert len(packages)==72
    context=ROOT/'.local/phase2/cbindgen-vendor-1';assert not context.exists(),'Reconcile actual partial vendor job before repeat'
    context.mkdir();(context/'cache').mkdir();(context/'vendor').mkdir()
    state={'scope':'Authenticated public source vendoring only; no host compilation','script_sha256':digest(Path(__file__)),'source_sha256':parent['sha256'],'cargo_lock_sha256':hashlib.sha256(body).hexdigest(),'started_unix':time.time(),'state':'acquiring','registry_crates':len(packages)}
    (context/'job.json').write_text(json.dumps(state,indent=2)+'\n')
    cached={}
    found=subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(ROOT/'.local/phase2')],text=True).splitlines()
    for name in found:
        p=Path(name)
        if p.suffix=='.crate' and '/registry/cache/' in name and p.is_file() and not p.is_symlink():cached.setdefault(p.name,[]).append(p)
    def acquire(row):
        filename=row['name']+'-'+row['version']+'.crate';destination=context/'cache'/filename
        candidates=cached.get(filename,[]);reuse=None
        for p in candidates:
            if digest(p)==row['sha256']:reuse=p;break
        if reuse:shutil.copyfile(reuse,destination)
        else:
            part=destination.with_suffix('.crate.part');assert not part.exists()
            command=['curl','--fail','--silent','--show-error','--location','--connect-timeout','15','--max-time','90','--output',str(part),'https://static.crates.io/crates/'+row['name']+'/'+filename]
            subprocess.run(command,check=True);assert digest(part)==row['sha256'];part.rename(destination)
        assert digest(destination)==row['sha256']
        return {**row,'reused_cache':str(reuse.relative_to(ROOT)) if reuse else None,'archive':str(destination.relative_to(ROOT))}
    with ThreadPoolExecutor(max_workers=4) as workers:acquired=list(workers.map(acquire,packages))
    (context/'acquired.json').write_text(json.dumps(acquired,indent=2)+'\n')
    for row in acquired:
        root=row['name']+'-'+row['version'];crate=ROOT/row['archive']
        with tarfile.open(crate) as t:
            members=t.getmembers();seen=set()
            for m in members:
                p=Path(m.name);assert p.parts and p.parts[0]==root and '..' not in p.parts and not p.is_absolute()
                assert m.isfile() or m.isdir(),'Source link/special file needs explicit review'
                assert str(p) not in seen;seen.add(str(p))
            t.extractall(context/'vendor',filter='data')
        directory=context/'vendor'/root;checksum=directory/'.cargo-checksum.json';assert not checksum.exists()
        files={str(p.relative_to(directory)):digest(p) for p in directory.rglob('*') if p.is_file() and not p.is_symlink()}
        checksum.write_text(json.dumps({'files':files,'package':row['sha256']},sort_keys=True)+'\n')
    verified=verify_vendor(context/'vendor',packages)
    artifact=bundle(context/'vendor',ROOT/'.local/sources/cbindgen-0.29.4-vendor.tar.gz')
    contract={'scope':'Exact authenticated cbindgen native build/test sources; no host compilation or product acceptance','registry':'registry+https://github.com/rust-lang/crates.io-index','host_source_compilations':0,'name':'cbindgen','version':parent['version'],'primary_source_sha256':parent['sha256'],'cargo_lock_sha256':state['cargo_lock_sha256'],'vendor_exit':0,'artifact':artifact,'packages':verified,'reused_archives':sum(r['reused_cache'] is not None for r in acquired),'downloaded_archives':sum(r['reused_cache'] is None for r in acquired),'producer_sha256':state['script_sha256']}
    config=ROOT/'config/phase2/cbindgen-crates.lock.json';assert not config.exists();config.write_text(json.dumps(contract,indent=2)+'\n')
    assert not any(r['name']=='cbindgen-vendor' for r in lock['components'])
    lock['components'].append({'name':'cbindgen-vendor','version':parent['version'],**artifact,'url':'generated:phase2_cbindgen_vendor/cbindgen-vendor','reference':'Exact Cargo.lock registry checksums from authenticated primary source; full archive/file verification, no host compiler','parent_source_sha256':parent['sha256'],'cargo_lock_sha256':state['cargo_lock_sha256'],'producer_sha256':state['script_sha256'],'registry_crates':len(packages),'integrity':'Each official registry archive SHA256 matched exact source lock; verified every extracted file and independent generated Cargo checksums before deterministic bundle','status':'source_verified'})
    path.write_text(json.dumps(lock,indent=2)+'\n')
    state.update(state='complete',artifact=artifact,reused_archives=contract['reused_archives'],downloaded_archives=contract['downloaded_archives']);(context/'result.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))

if __name__=='__main__':main()
