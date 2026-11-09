"""Require unchanged original calendar tests plus actual typed native consumer."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/libical-4.0.5');work=Path('/mnt/lfs/sources/phase2/work/libical-1');log=Path('/var/log/toddy/phase2')
 assert digest(source/'toddy-build.sh')=='d4f5a6168eafe00f60aec8c2341a24400691c246dc460909507c7860c0c283b5'
 assert digest(source/'toddy-probe.c')=='34d93fbf4421f53871835679baac2cfb8c9a60eeb263f0e0897a65622b636a91'
 assert (log/'libical-1.exit').read_text().strip()=='8' and (log/'libical-finish-2.exit').read_text().strip()=='0'
 assert json.loads((log/'libical-1.job.json').read_text())['command'][2:]==[str(source),str(work),'bash','/src/toddy-build.sh']
 assert json.loads((log/'libical-finish-2.job.json').read_text())['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2/libical_finish.py').read_text()]
 result=json.loads((work/'stage-results.json').read_text());assert result['compile_exit']==result['stage_exit']==0
 cases=ET.parse(work/'original-tests.xml').findall('.//testcase');passed=[c.get('name') for c in cases if c.find('failure') is None and c.find('skipped') is None and c.find('error') is None]
 assert len(cases)==66 and len(passed)==65 and result['reused_original_tests']==passed and {c.get('name') for c in cases}-set(passed)=={'recur'}
 repaired=result['repaired_original_test'];assert repaired['name']=='recur' and repaired['exit']==0 and repaired['fixture_contents_unchanged'] and repaired['private_fixture_removed'] and not (work/'recur-private-2.txt').exists()
 assert repaired['source_fixture_sha256']==digest(source/'test-data/recur.txt') and repaired['log_sha256']==digest(work/'recur-2.log') and (work/'recur-2.exit').read_text().strip()=='0'
 assert result['consumer']=={'UTF8_calendar_roundtrip':True,'UTC_daily_recurrence_count':3,'invalid_document_refused':True,'prior_state_preserved':True,'recovery_cycles':2}
 for base,key in [('compile','unchanged_original_elfs'),('stage','stage_sha256')]:
  for name,sha in result[key].items():assert digest(work/base/name)==sha
 assert (log/'libical-consumer-3.exit').read_text().strip()=='0'
 assert json.loads((log/'libical-consumer-3.job.json').read_text())['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2/libical_consumer.py').read_text(),(root/'scripts/build/phase2/libical-probe.c').read_text()]
 corrected=json.loads((work/'consumer-3.json').read_text());assert corrected['exit']==0 and corrected['consumer']==result['consumer'] and corrected['original_ELFs_unchanged'] and corrected['stage_unchanged']
 assert corrected['source_sha256']==digest(root/'scripts/build/phase2/libical-probe.c')==digest(work/'native-probe-3.c') and corrected['binary_sha256']==digest(work/'native-probe-3')
 return result
