"""Correct own borrowed-RRULE lifetime; never rebuild/reinstall the library."""
from pathlib import Path
import hashlib,json,subprocess,sys
p=Path('/build');assert not (p/'consumer-3.json').exists()
stage=json.loads((p/'stage-results.json').read_text())
def digest(f):
 with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
for base,key in [('compile','unchanged_original_elfs'),('stage','stage_sha256')]:
 for name,sha in stage[key].items():assert digest(p/base/name)==sha
source=p/'native-probe-3.c';source.write_text(sys.argv[1])
assert 'icalrecurrencetype_unref(rule)' not in source.read_text()
subprocess.run(['cc',str(source),'-I/usr/include','-lical','-o','/build/native-probe-3'],check=True)
env={**__import__('os').environ,'MALLOC_CHECK_':'3'}
r=subprocess.run(['/build/native-probe-3'],env=env,capture_output=True,text=True,timeout=15)
(p/'native-consumer-3.stdout').write_text(r.stdout);(p/'native-consumer-3.stderr').write_text(r.stderr);assert r.returncode==0
for base,key in [('compile','unchanged_original_elfs'),('stage','stage_sha256')]:
 for name,sha in stage[key].items():assert digest(p/base/name)==sha
(p/'consumer-3.json').write_text(json.dumps({'scope':'Corrected own borrowed RRULE lifetime against already installed libical; first consumer result superseded, original libraries/tests/stage unchanged','consumer':json.loads(r.stdout),'source_sha256':digest(source),'binary_sha256':digest(p/'native-probe-3'),'original_ELFs_unchanged':True,'stage_unchanged':True,'exit':r.returncode},indent=2)+'\n')
