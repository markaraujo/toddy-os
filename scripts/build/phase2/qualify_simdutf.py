"""Bind full default Unicode originals and explicit unsupported CPU notes."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/simdutf-9.0.0');w=Path('/mnt/lfs/sources/phase2/work/simdutf-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','simdutf-build.sh'),('toddy-probe.py','simdutf-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='fd2ce975f29809a975a8da8843cfb3a7265af3f71be548f199d23cf65e101764'
 assert (l/'simdutf-1.exit').read_text().strip()=='0'
 assert json.loads((l/'simdutf-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 cases=ET.parse(w/'original-tests.xml').getroot().findall('.//testcase');assert len(cases)==91 and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
 notes=[line.strip() for c in cases for line in ''.join(c.itertext()).splitlines() if re.search('skip|unsupported|not support',line,re.I)]
 assert len(notes)==79 and set(notes)=={'Implementation icelake is unsupported by the current processor.'}
 cache=(w/'compile/CMakeCache.txt').read_text();assert 'SIMDUTF_ALWAYS_INCLUDE_FALLBACK:BOOL=ON' in cache and 'SIMDUTF_FAST_TESTS:BOOL=OFF' in cache
 assert r['original_tests']==[{'name':c.get('name'),'status':c.get('status')} for c in cases]
 assert len(r['artifacts'])==193 and len(r['stage_sha256'])==49
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 assert r['consumer']=={'Unicode_PT_emoji_roundtrip':True,'codepoint_and_surrogate_lengths':True,'overlong_UTF8_refused':True,'unpaired_UTF16_refused':True,'reset_recovery_cycles':2,'CMake_discovered_version':'9.0.0','shared_library_consumer':True,'terminal_or_GUI_tested':False}
 return r
