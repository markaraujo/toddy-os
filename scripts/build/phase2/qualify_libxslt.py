"""Qualify a build SDK without hiding make-check's swallowed DocBook differences."""
from pathlib import Path
import hashlib,json,re

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def review(log,source):
 text=log.read_text();assert re.findall(r'^Total (\d+) tests, no errors$',text,re.M)==['748']
 hunks=re.findall(r'^\d+[acd]\d+$',text,re.M);assert hunks==['157c157','398c398','158c158','64c64']
 lines=[s for s in text.splitlines() if s.startswith(('< ','> '))];assert len(lines)==8
 for expected,actual in zip(lines[::2],lines[1::2]):
  assert expected.startswith('< ') and actual.startswith('> ')
  assert actual.count('           http://sourceware.cygnus.com/docbook-tools/')>=1
  assert actual[2:].replace('           http://sourceware.cygnus.com/docbook-tools/','http://sourceware.cygnus.com/docbook-tools/')==expected[2:]
 assert not re.search(r'Permission denied|Result for .* failed|Error for .* failed|Total \d+ tests, [1-9]\d* errors',text)
 fixture=source/'tests/docbook/test/gdp-handbook.xml';assert 'url="\n          http://sourceware.cygnus.com/docbook-tools/"' in fixture.read_text()
 return {'make_check_exit':0,'core_driver_reported_cases':748,'core_driver_reported_errors':0,'DocBook_golden_differences':4,'DocBook_differences_accepted':False,'all_original_cases_passed_claim':False,'difference_scope':'Source fixture multiline URL indentation retained in four HTML/XHTML/FO/chunk golden comparisons; no goldens/source changed. Build SDK only; not a general DocBook renderer qualification.','source_conditional_German_locale_branch':'Not independently asserted; no separate locale pass claim','original_log_sha256':digest(log),'fixture_sha256':digest(fixture)}
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libxslt-1.1.45');w=Path('/mnt/lfs/sources/phase2/work/libxslt-1');l=Path('/var/log/toddy/phase2')
 assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/libxslt-build.sh').read_bytes()
 assert (s/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/libxslt-probe.py').read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='9acfe68419c4d06a45c550321b3212762d92f41465062ca4ea19e632ee5d216e'
 assert (l/'libxslt-1.exit').read_text().strip()=='0' and (w/'original-tests.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==r['original_check_exit']==0
 assert len(r['artifacts'])==41 and len(r['stage_sha256'])==92
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 assert r['consumer']=={'xsltproc_version':'1.1.45','UTF8_transform':True,'malformed_XML_refused':True,'EXSLT_write_refused_no_effect':True,'reset_recovery_cycles':2,'selected_flags':['nonet','nowrite','nomkdir','maxdepth128','maxvars4096'],'GUI_or_general_CLI_default_sandbox_claim':False}
 r['original_review']=review(w/'original-tests.log',s)
 return r
