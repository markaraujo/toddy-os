#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PYTHONDONTWRITEBYTECODE=1
# Upstream's make backend writes beside source. The entire compiler tree is a
# private worker copy; /src and installed inputs remain read-only.
cp -R /src /build/source
cd /build/source/nss
make -j4 BUILD_OPT=1 NSPR_INCLUDE_DIR=/usr/include/nspr USE_SYSTEM_ZLIB=1 \
    ZLIB_LIBS=-lz NSS_ENABLE_WERROR=0 NSS_USE_SYSTEM_SQLITE=1 USE_64=1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,xml.etree.ElementTree as ET
p=Path('/build');dirs=[d for d in (p/'source/dist').glob('Linux*') if (d/'bin/certutil').is_file()];assert len(dirs)==1
dist=dirs[0];env={**os.environ,'LD_LIBRARY_PATH':str(dist/'lib'),'NSS_DEFAULT_DB_TYPE':'sql'};rows=[]
# Bounded original crypto/DER/container/API programs; no external network or
# full potentially hanging tests/all.sh, as documented by the frozen book.
for name in ['base_gtest','der_gtest','cryptohi_gtest','freebl_gtest','util_gtest']:
 with tempfile.TemporaryDirectory(prefix='nss-original-',dir='/build') as directory:
  db=Path(directory);r=subprocess.run([str(dist/'bin/certutil'),'-N','-d','sql:'+directory,'--empty-password'],env=env,capture_output=True,timeout=30);assert r.returncode==0
  report=p/(name+'.xml')
  with (p/(name+'.log')).open('x') as log:r=subprocess.run([str(dist/'bin'/name),'-s',str(p/'source/nss/gtests'/name),'-d','sql:'+directory,'-w','--gtest_output=xml:'+str(report)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  assert report.is_file();cases=ET.parse(report).findall('.//testcase');assert cases
  row={'name':name,'exit':r.returncode,'passed':len([c for c in cases if c.find('failure') is None and c.find('skipped') is None and c.get('status')=='run']),'skipped':[c.get('classname')+'.'+c.get('name') for c in cases if c.find('skipped') is not None or c.get('status')!='run'],'failures':[c.get('classname')+'.'+c.get('name') for c in cases if c.find('failure') is not None]};rows.append(row)
  (p/'original-results.json').write_text(json.dumps(rows,indent=2)+'\n');assert r.returncode==0 and not row['failures']
 assert not Path(directory).exists()
# Stage the book's minimal dynamic SDK/runtime/three utilities. Keep bundled
# roots until a separately qualified p11-kit/make-ca provider transaction.
stage=Path('/stage');(stage/'usr/lib/pkgconfig').mkdir(parents=True);(stage/'usr/include/nss').mkdir(parents=True);(stage/'usr/bin').mkdir(parents=True)
import shutil
for pattern,mode in [('*.so',0o755),('*.chk',0o644)]:
 for f in (dist/'lib').glob(pattern):shutil.copyfile(f,stage/'usr/lib'/f.name);(stage/'usr/lib'/f.name).chmod(mode)
for base in ['public','private']:
 for f in (p/'source/dist'/base/'nss').iterdir():
  assert f.is_file();shutil.copyfile(f,stage/'usr/include/nss'/f.name)
for name in ['certutil','nss-config','pk12util']:shutil.copyfile(dist/'bin'/name,stage/'usr/bin'/name);(stage/'usr/bin'/name).chmod(0o755)
shutil.copyfile(dist/'lib/pkgconfig/nss.pc',stage/'usr/lib/pkgconfig/nss.pc')
env={**os.environ,'PKG_CONFIG_PATH':'/stage/usr/lib/pkgconfig','LD_LIBRARY_PATH':'/stage/usr/lib'}
flags=subprocess.check_output(['pkg-config','--cflags','--libs','nss'],env=env,text=True).split()
subprocess.run(['cc','/src/toddy-probe.c','-I/stage/usr/include/nss','-L/stage/usr/lib',*flags,'-o','/build/native-probe'],env=env,check=True)
r=subprocess.run(['/build/native-probe'],env=env,capture_output=True,text=True,timeout=30);(p/'native-consumer.json').write_text(r.stdout);(p/'native-consumer.stderr').write_text(r.stderr);assert r.returncode==0
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
result={'scope':'Five bounded original crypto/DER/container/API drivers and native SHA256/random/AES-GCM/tamper/refusal/recovery; full suite/PK11 database/TLS/trust-store/remote network/GNOME pending','compile_exit':0,'stage_exit':0,'original_tests':rows,'consumer':json.loads(r.stdout),'root_provider':'Upstream bundled roots retained; qualified p11-kit/make-ca integration pending','artifacts':{str(f.relative_to(p/'source')):digest(f) for f in (p/'source').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(stage)):digest(f) for f in stage.rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
