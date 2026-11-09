"""Resume only three TLS originals after exposing real read-only factory roots."""
from pathlib import Path
import hashlib,json,subprocess,os,errno
p=Path('/build')
assert not (p/'stage-results.json').exists() and not list(Path('/stage').iterdir())
assert not (p/'initial-testlog-1.json').exists(),'Inspect previous continuation; no replay'
def digest(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
original=p/'compile/meson-logs/testlog.json';initial=[json.loads(s) for s in original.read_text().splitlines() if s.strip()]
passed={'glib-networking:environment-libproxy','glib-networking:gnome','glib-networking:certificate-gnutls'}
failed={'glib-networking:file-database-gnutls','glib-networking:connection-gnutls','glib-networking:connection-gnutls-tls1.2'}
assert len(initial)==6 and {r['name'] for r in initial if r['result']=='OK' and r['returncode']==0}==passed
assert {r['name'] for r in initial if r['result']=='FAIL' and r['returncode']==-6}==failed
assert all('System trust contains zero trusted certificates' in r['stderr'] for r in initial if r['name'] in failed)
before={str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
(p/'initial-testlog-1.json').write_bytes(original.read_bytes())
(p/'ELFs-before-TLS-2.json').write_text(json.dumps(before,indent=2)+'\n')
for name in ['/etc/pki/anchors','/etc/ssl/certs']:
    try:
        f=os.open(name+'/toddy-forbidden-write',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except OSError as error:assert error.errno in [errno.EROFS,errno.EACCES]
    else:os.close(f);raise AssertionError('Writable trust input')
with (p/'TLS-remaining-2.log').open('x') as log:
    r=subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--print-errorlogs','-j1',*sorted(failed)],stdout=log,stderr=subprocess.STDOUT)
(p/'TLS-remaining-2.exit').write_text(str(r.returncode)+'\n')
remaining=[json.loads(s) for s in original.read_text().splitlines() if s.strip()]
(p/'remaining-testlog-2.json').write_bytes(original.read_bytes())
assert {r['name'] for r in remaining}==failed and len(remaining)==3
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
assert r.returncode==0 and all(t['result']=='OK' and t['returncode']==0 for t in remaining)
tests=[r for r in initial if r['name'] in passed]+remaining
subprocess.run(['meson','install','-C','/build/compile','--destdir','/stage','--no-rebuild'],check=True)
subprocess.run(['gio-querymodules','/stage/usr/lib/gio/modules'],check=True)
flags=subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True).split()
subprocess.run(['cc','/src/toddy-probe.c',*flags,'-o','/build/native-probe'],check=True)
env={**os.environ,'GIO_MODULE_DIR':'/stage/usr/lib/gio/modules','GIO_USE_TLS':'gnutls'}
r=subprocess.run(['/build/native-probe'],env=env,text=True,capture_output=True,timeout=30)
(p/'native-consumer.json').write_text(r.stdout);(p/'native-consumer.stderr').write_text(r.stderr);assert r.returncode==0
assert all(digest(p/'compile'/name)==sha for name,sha in before.items())
result={'scope':'Three original proxy/certificate passes reused; only three affected TLS originals repeated with actual read-only installed factory roots. Six enabled originals now pass; initial missing-root failures retained. Public GIO/backend/default trust/malformed certificate refusal/recovery. Remote network/DTLS/native GNOME/shared installed cache pending.', 'compile_exit':0,'stage_exit':0,'original_tests':[{k:t[k] for k in ['name','result','returncode']} for t in tests], 'initial_failed_tests_retained':True,'public_trust_readonly':True,'prior_ELFs_unchanged':True,'consumer':json.loads(r.stdout),'artifacts':before,'stage_sha256':{str(f.relative_to(p/'stage')):digest(f) for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
