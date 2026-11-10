"""Apply only book reference-cache correction and own reset probe; reuse regex."""
from pathlib import Path
import hashlib,json,os,subprocess

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main(probe,correction):
 w=Path('/build');assert not (w/'stage-results.json').exists()
 assert (w/'original-tests.exit').read_text().strip()=='0'
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
 before={'artifacts':hashes(w/'compile',True),'stage_sha256':hashes(w/'stage')}
 p=w/'probe-3';p.mkdir();(p/'probe.py').write_text(probe);(p/'before.json').write_text(json.dumps(before,indent=2)+'\n');(p/'schema.py').write_text(correction)
 namespace={};exec(correction,namespace);schema=namespace['correct']()
 env=os.environ.copy()
 with (p/'consumer.json').open('x') as out:r=subprocess.run(['python3',str(p/'probe.py'),'/stage',str(p/'consumer')],env=env,stdout=out,timeout=90)
 (p/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 bad=subprocess.run(['/stage/usr/bin/gnome-terminal','--toddy-invalid-option'],capture_output=True,text=True,timeout=15);assert bad.returncode!=0 and 'unknown option' in bad.stderr.lower() and '--toddy-invalid-option' in bad.stderr
 after=hashes(w/'stage');assert hashes(w/'compile',True)==before['artifacts']
 changed={key for key in set(after)|set(before['stage_sha256']) if after.get(key)!=before['stage_sha256'].get(key)};assert changed=={'usr/lib/gnome-terminal/gschemas.compiled','usr/share/doc/gnome-terminal/external-schema-paths.patch'}
 result={'scope':'Frozen GNOME Terminal3.60.0 with same-book five external proxy path correction in separate reference cache, all compiled ELFs/original regex unchanged. Actual staged client/unknown option and private DConf Unicode/navy preferences/malformed boolean refusal/persistence across buses/reset to declared defaults/system font preservation. Own initial reset assertion failure retained. No native installed package/widget/window/focus/PTY/login acceptance; stock schema cache integration pending.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'consumer.json').read_text()),'actual_unknown_option_error_verified':True,'schema_correction':schema,'probe_only_recovery':{'compiled_ELFs_unchanged':True,'unrelated_stage_files_unchanged':True,'original_failures_retained':True,'corrected_probe_sha256':hashlib.sha256(probe.encode()).hexdigest()},'artifacts':before['artifacts'],'stage_sha256':after}
 (w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
