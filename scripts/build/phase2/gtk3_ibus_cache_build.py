"""Query owned modules read-only and preserve every prior IM registration."""
from pathlib import Path
import hashlib,json,os,shlex,subprocess
P=Path('/build');S=Path('/src');r=json.loads((S/'toddy-input.json').read_text())
assert os.geteuid()==101 and not (P/'test-results.json').exists() and not (P/'immodules.cache').exists()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def entries(text):
 result={};current=None
 for line in text.splitlines():
  if not line.strip() or line.startswith('#'):continue
  row=shlex.split(line)
  if len(row)==1:
   assert row[0].startswith('/usr/lib/gtk-3.0/3.0.0/immodules/') and row[0] not in result
   current=row[0];result[current]=[]
  else:
   assert current and len(row)==5;result[current].append(row)
 assert result and all(result.values());return result
assert digest(S/'baseline.cache')==r['old_cache_sha256'] and digest(Path(r['tool']))==r['tool_sha256']
for name,row in r['modules'].items():assert digest(Path(name))==row['sha256']
with (P/'immodules.cache').open('xb') as out,(P/'query.stderr').open('xb') as err:
 process=subprocess.run([r['tool'],*sorted(r['modules'])],stdout=out,stderr=err)
assert process.returncode==0 and not (P/'query.stderr').read_bytes()
old=entries((S/'baseline.cache').read_text());new=entries((P/'immodules.cache').read_text())
assert len(old)==11 and len(new)==12 and set(new)==set(r['modules'])
assert all(new.get(name)==rows for name,rows in old.items())
added='/usr/lib/gtk-3.0/3.0.0/immodules/im-ibus.so';assert set(new)-set(old)=={added}
assert new[added]==[['ibus','IBus (Intelligent Input Bus)','ibus','','ja:ko:zh:*']]
for name,row in r['modules'].items():assert digest(Path(name))==row['sha256']
(P/'test-results.json').write_text(json.dumps({'scope':'Actual installed GTK3 query tool loads twelve owned IM modules read-only; eleven previous module registrations preserved and IBus added. No display/focus/GNOME keyboard claim.','query_exit':process.returncode,'old_module_count':len(old),'new_module_count':len(new),'entries':new,'modules':r['modules'],'tool_sha256':r['tool_sha256'],'cache_sha256':digest(P/'immodules.cache'),'baseline_cache_sha256':r['old_cache_sha256']},indent=2)+'\n')
