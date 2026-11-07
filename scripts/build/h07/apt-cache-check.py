#!/usr/bin/env python3
"""Exercise actual apt-ftparchive Berkeley cache and recoverable index publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--ftparchive',default='/usr/bin/apt-ftparchive')
    args=parser.parse_args()
    base=args.work.absolute()
    if base.exists() or base.parent.resolve()!=base.parent:
        raise ValueError('Fresh physical cache-test workspace required')
    base.mkdir(mode=0o755)
    pool=base/'pool';pool.mkdir()
    stage=base/'package';(stage/'DEBIAN').mkdir(parents=True)
    (stage/'usr/share/toddy-cache').mkdir(parents=True)
    (stage/'DEBIAN/control').write_text('Package: toddy-cache-probe\nVersion: 1\nArchitecture: all\nMaintainer: Toddy OS <test@example.invalid>\nDescription: Disposable Berkeley cache verification\n')
    payload=stage/'usr/share/toddy-cache/value';payload.write_bytes(b'first native payload\n')
    deb=pool/'toddy-cache-probe_1_all.deb'
    records=[]
    (base/'config-parts').mkdir()
    config=base/'apt.conf'
    config.write_text('Dir::Etc::main "-";\nDir::Etc::parts "'+str(base/'config-parts')+'";\n')
    os.environ['APT_CONFIG']=str(config)
    status=Path('/var/lib/dpkg/status');before=sha(status)

    def run(label,argv,expected=0,allow_cache_error=False):
        with (base/(label+'.out')).open('xb') as out,(base/(label+'.err')).open('xb') as err:
            result=subprocess.run(argv,cwd=base,stdout=out,stderr=err,timeout=120)
        records.append({'step':label,'exit':result.returncode,'stdout_sha256':sha(base/(label+'.out')),
                        'stderr_sha256':sha(base/(label+'.err'))})
        if not allow_cache_error and any(line.startswith(('E:','W:','BDB')) for line in (base/(label+'.err')).read_text().splitlines()):
            raise ValueError(label+' emitted diagnostics; candidate index must not be published')
        if result.returncode!=expected:raise ValueError(label+' unexpected exit '+str(result.returncode))
        return base/(label+'.out')

    def build(label):
        run(label,['dpkg-deb','-Znone','--build',str(stage),str(deb)])

    cache=base/'cache.db'
    def command(directory='pool',database=cache):
        return [args.ftparchive,'--db='+str(database),'-o','APT::FTPArchive::AlwaysStat=true','packages',directory]

    def verify(index,directory='pool'):
        entries={}
        for paragraph in index.read_text().strip().split('\n\n'):
            row={}
            for line in paragraph.splitlines():
                if not line.startswith(' ') and ': ' in line:
                    key,value=line.split(': ',1);row[key]=value
            if not row:continue
            filename=row['Filename'];path=(base/filename).resolve()
            if path.parent!=base/directory:raise ValueError('Unexpected indexed file')
            assert row['Package']=='toddy-cache-probe' and row['Version']=='1'
            assert int(row['Size'])==path.stat().st_size and row['SHA256']==sha(path)
            assert filename not in entries
            entries[filename]=row
        assert len(entries)==len(list((base/directory).glob('*.deb'))) and entries
        return entries

    result={'complete':False,'full_berkeley_suite_accepted':False,'steps':records}
    try:
        build('build-original')
        cold=run('cold',command());initial=verify(cold)
        assert cache.stat().st_size>0
        warm=run('reopen',command());assert verify(warm)==initial
        published=base/'Packages';shutil.copyfile(warm,published)
        old_hash=sha(deb);old_time=deb.stat().st_mtime
        payload.write_bytes(b'changed native payload, same version\n')
        build('build-replaced');os.utime(deb,(old_time+2,old_time+2))
        refreshed=run('refresh',command());changed=verify(refreshed)
        assert sha(deb)!=old_hash and changed!=initial
        os.replace(refreshed,published);published_hash=sha(published)
        # Real process kill after observing its open Berkeley cache descriptor.
        # Hardlinks keep disk use small while giving the consumer measurable work.
        payload.write_bytes(bytes(range(256))*8192);build('build-interruption-input')
        bulk=base/'bulk';bulk.mkdir()
        for number in range(128):os.link(deb,bulk/('%04d.deb'%number))
        interrupted_cache=base/'interrupted.db'
        with (base/'interrupted.out').open('xb') as out,(base/'interrupted.err').open('xb') as err:
            process=subprocess.Popen(command('bulk',interrupted_cache),cwd=base,stdout=out,stderr=err)
            deadline=time.monotonic()+15;observed=False
            while process.poll() is None and time.monotonic()<deadline:
                for fd in (Path('/proc')/str(process.pid)/'fd').glob('*'):
                    try:
                        if os.readlink(fd)==str(interrupted_cache):observed=True;break
                    except FileNotFoundError:pass
                if observed:break
                time.sleep(.001)
            if not observed:
                process.kill();process.wait();raise ValueError('Did not observe actual open cache before interruption')
            process.kill();code=process.wait(timeout=10)
        assert code==-signal.SIGKILL and sha(published)==published_hash
        records.append({'step':'interrupt-open-cache','exit':code,'open_cache_observed':observed,
                        'published_index_unchanged':True})
        if interrupted_cache.exists():interrupted_cache.rename(base/'interrupted.db.preserved')
        rebuilt=run('rebuild-after-interruption',command('bulk',interrupted_cache));verify(rebuilt,'bulk')
        # Corrupt only disposable metadata, retain it and rebuild from .deb files.
        cache.write_bytes(b'not a Berkeley database\n'*512)
        # Frozen writer.cc dumps constructor errors, so actual ftparchive can
        # return zero with E:/BDB diagnostics. Detect those instead of trusting
        # the exit code; preserve the previous index until a clean rebuild.
        run('reject-corrupt-cache',command(),expected=0,allow_cache_error=True)
        diagnostics=(base/'reject-corrupt-cache.err').read_text()
        assert 'E: Unable to open DB file ' in diagnostics and 'BDB' in diagnostics
        assert sha(published)==published_hash
        records.append({'step':'reject-diagnostic-bearing-index','accepted':False,
                        'raw_consumer_exit':0,'published_index_unchanged':True})
        cache.rename(base/'cache.db.corrupt-preserved')
        repaired=run('rebuild-after-corruption',command());verify(repaired)
        os.replace(repaired,published)
        assert sha(status)==before
        result.update(complete=True,native_status_unchanged=True,
                      published_index_sha256=sha(published),consumer_sha256=sha(Path(args.ftparchive).resolve()),
                      scope='Real cache create/reopen/refresh, SIGKILL, corruption rejection and source-derived rebuild')
    finally:
        (base/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
