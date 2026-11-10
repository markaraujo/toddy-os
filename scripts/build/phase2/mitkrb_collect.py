"""Only fix the own staged linker search; reuse original successful tests/stage."""
from pathlib import Path
import hashlib,json,subprocess

def main(recipe):
 w=Path('/build');receipt=w/'before-collect-3.json';assert not receipt.exists() and not (w/'stage-results.json').exists()
 def files(base,elf=False):
  return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
 before={'artifacts':files(w/'compile',True),'stage_sha256':files(Path('/stage'))}
 original=json.loads((w/'before-finish-2.json').read_text());assert all(before['artifacts'][k]==v for k,v in original['artifacts'].items())
 assert hashlib.sha256((w/'original-crypto-tests.log').read_bytes()).hexdigest()==original['crypto_log_sha256']
 logs={n:hashlib.sha256((w/n).read_bytes()).hexdigest() for n in ['original-crypto-tests.log','original-gss-c-tests.log','original-db2-tests.log','original-stage.log']}
 assert (w/'original-gss-c-tests.log').read_text()=='t_invalid\nt_oid\nt_prf\nt_imp_name\nreload\n'
 receipt.write_text(json.dumps({**before,'reused_logs':logs},indent=2)+'\n')
 marker='cc /src/toddy-probe.c';assert recipe.count(marker)==1
 subprocess.run(['bash','-euo','pipefail','-c',recipe[recipe.index(marker):]],check=True)
 r=json.loads((w/'stage-results.json').read_text());assert r['artifacts']==before['artifacts'] and r['stage_sha256']==before['stage_sha256']
 assert all(hashlib.sha256((w/n).read_bytes()).hexdigest()==sha for n,sha in logs.items())
