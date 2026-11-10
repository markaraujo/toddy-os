"""Bind original archive-security fixtures and corrected own UTF8 consumer only."""
from pathlib import Path
import hashlib,json,re

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gnome-autoar-0.4.5');w=Path('/mnt/lfs/sources/phase2/work/gnome-autoar-1');l=Path('/var/log/toddy/phase2')
 prep=json.loads((s/'toddy-prepared.json').read_text());assert prep['source_sha256']=='838c5306fc38bfaa2f23abe24262f4bf15771e3303fb5dcb74f5b9c7a615dabe'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['reused_libarchive_version']=='3.8.11'
 assert (w/'original-tests.exit').read_text().strip()=='0';text=(w/'original-tests.log').read_text();cases=re.findall(r'^ok\s+\d+[^\n]*',text,re.M);assert len(cases)==22 and not re.search(r'^not ok|#\s*SKIP',text,re.M);assert cases==r['original_unit_cases']
 rows=json.loads((w/'original-registered-tests.json').read_text());assert len(rows)==1 and rows[0]['name']=='test-extract-unit'
 assert r['original_fixture_verification']==json.loads((w/'original-fixtures-verified.json').read_text())
 fixture=r['original_fixture_verification'];assert fixture['source_unchanged'] and fixture['private_input_reference_unchanged'] and fixture['original_binary_unmodified'] and fixture['tmp_symlink_escape_not_created'] and fixture['fixture_entries']==130
 assert digest(w/'original-fixtures-manifest.json')==fixture['manifest_sha256']
 assert len(r['artifacts'])==19 and len(r['stage_sha256'])==21
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 if (l/'gnome-autoar-probe-3.exit').exists():
  assert (l/'gnome-autoar-build-2.exit').read_text().strip()=='134' and 'Pathname cannot be converted from UTF-8 to current locale' in (l/'gnome-autoar-build-2.log').read_text()
  assert digest(s/'toddy-build.sh')==prep['recipe_sha256']=='76619b8c56c9ec92dd40752cb1c3cfedcb6cc239bea7d248be7c3da7d13c0031'
  assert digest(s/'toddy-probe.c')=='2f381e13b7722f3e44d50c30bcbb0ed906f4320c3af128631b231dd1da8adb80'
  assert (l/'gnome-autoar-probe-3.exit').read_text().strip()=='0'
  probe=(root/'scripts/build/phase2/gnome-autoar-probe.c').read_text();assert (w/'probe-3/probe.c').read_text()==probe
  code=(root/'scripts/build/phase2/gnome_autoar_probe_resume.py').read_text()+'\nmain('+repr(probe)+')\n'
  assert json.loads((l/'gnome-autoar-probe-3.job.json').read_text())['command'][-3:]==['python3','-c',code]
  before=json.loads((w/'probe-3/before.json').read_text());assert all(r[k]==before[k] for k in ['artifacts','stage_sha256']) and r['probe_only_recovery']['compile_and_stage_unchanged']
 else:
  assert (l/'gnome-autoar-1.exit').read_text().strip()=='0'
  assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/gnome-autoar-build.sh').read_bytes()
  assert (s/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/gnome-autoar-probe.c').read_bytes()
 assert r['consumer']=={'UTF8_ZIP_extractions':4,'empty_archive_refusals':2,'precancelled_no_destination':2,'recovery_cycles':2,'source_archive_retained':True,'GUI_or_mid_extraction_Stop_tested':False}
 assert r['GI_consumer']=={'namespace':'GnomeAutoar0.1/GnomeAutoarGtk0.1','GI_type':'AutoarExtractor','widget_tested':False}
 return r
