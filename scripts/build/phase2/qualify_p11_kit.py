"""Qualify actual original PKCS11 fixtures without treating nested skips as passes."""
import hashlib,json,re
from pathlib import Path
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/p11-kit-0.26.5');work=Path('/mnt/lfs/sources/phase2/work/p11-kit-1');log=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','p11-kit-build.sh'),('toddy-probe.c','p11-kit-probe.c')]:assert (source/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (log/'p11-kit-1.exit').read_text().strip()=='0'
 assert json.loads((log/'p11-kit-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
 assert len(rows)==67 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
 assert result['original_tests']==[{k:r[k] for k in ['name','result','returncode']} for r in rows]
 skips=[{'program':r['name'],'line':s} for r in rows for s in r.get('stdout','').splitlines() if re.match(r'^ok \d+.*#\s*SKIP',s,re.I)]
 assert skips==[{'program':'p11-kit:test-compat','line':'ok 4 /compat/getprogname # SKIP cannot perform getprogname test: path contains a symlink'},{'program':'p11-kit:test-server.sh','line':'ok 1 # skip test_server_access: p11tool not found'}]
 assert sum(len(re.findall(r'^ok \d+',r.get('stdout',''),re.M)) for r in rows)==1079
 assert result['consumer']=={'typed_PKCS11_URI_roundtrip':True,'bad_scheme_and_encoding_refused':True,'recovery_cycles':2,'credentials_loaded':False}
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 return {'programs':67,'observed_tap_pass_lines':1077,'upstream_nested_skips':skips,'consumer':result['consumer']}
