"""Bind original private mock-portal tests separately from real desktop acceptance."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libportal-0.9.1');w=Path('/mnt/lfs/sources/phase2/work/libportal-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','libportal-build.sh'),('toddy-probe.c','libportal-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='de801ee349ed3c255a9af3c01b1a401fab5b3fc1c35eb2fd7dfb35d4b8194d7f'
 assert (l/'libportal-1.exit').read_text().strip()=='0' and (w/'original-tests.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0 and rows[0]['name']=='libportal:pytest'
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 cases=ET.parse(w/'original-pytest.xml').getroot().findall('.//testcase');assert len(cases)==61 and not any(c.find(k) is not None for c in cases for k in ['failure','error','skipped'])
 assert r['original_pytest_cases']==[{'name':c.get('name'),'failure':False,'error':False,'skipped':False} for c in cases]
 assert len(r['artifacts'])==33 and len(r['stage_sha256'])==42
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 assert r['consumer']=={'private_session_bus':True,'normal_nonFlatpak_nonSnap_context':True,'construct_release_cycles':2,'desktop_backend_or_permission_UI_tested':False}
 assert r['GI_consumers']==[{'namespace':'XdpGtk'+v+'1.0','base_GI_type':'XdpPortal','GTK_backend_symbol_loaded':True,'widget_or_parent_export_tested':False} for v in ['3','4']]
 return r
