"""Correct only the own CLI expectation, preserving all approved binary/test inputs."""
from pathlib import Path
import hashlib,json,os,subprocess,sys

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
w=Path('/build');r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['consumer_exit']==1
assert len(r['original_tests'])==5 and all(x['exit']==0 for x in r['original_tests'])
assert hashes(w/'compile',True)==r['artifacts'] and hashes(Path('/stage'))==r['stage_sha256']
name=sys.argv[2] if len(sys.argv)>2 else 'probe-5';assert name in ['probe-5','probe-7']
out=w/name;out.mkdir();probe=sys.argv[1];(out/'probe.py').write_text(probe)
with (out/'consumer.json').open('xb') as stream,(out/'consumer.stderr').open('xb') as error:child=subprocess.run(['python3',str(out/'probe.py'),'/stage/usr/bin/exiv2',str(out/'consumer')],env=dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib'),stdout=stream,stderr=error)
assert hashes(w/'compile',True)==r['artifacts'] and hashes(Path('/stage'))==r['stage_sha256']
result={'scope':'Own metadata/reset/XMP parser consumer only; all previously passed changed-profile original programs/compiled/stage inputs retained, no replay.','consumer_exit':child.returncode,'consumer':json.loads((out/'consumer.json').read_text()) if child.returncode==0 else None,'all_compiled_and_stage_hashes_unchanged':True}
(out/'result.json').write_text(json.dumps(result,indent=2)+chr(10));print(json.dumps(result));assert child.returncode==0
