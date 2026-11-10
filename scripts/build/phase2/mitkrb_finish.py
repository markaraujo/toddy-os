"""Continue after the overly broad GSS make target without rebuilding/retesting crypto."""
from pathlib import Path
import hashlib,json,subprocess

def artifacts():
 w=Path('/build/compile')
 return {str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}

def main(recipe):
 w=Path('/build');receipt=w/'before-finish-2.json';assert not receipt.exists() and (w/'stage').is_dir() and not list((w/'stage').iterdir())
 assert 'make runenv.py' in (w/'original-gss-tests.log').read_text()
 crypto=w/'original-crypto-tests.log';sha=hashlib.sha256(crypto.read_bytes()).hexdigest()
 before=artifacts();assert before
 receipt.write_text(json.dumps({'artifacts':before,'crypto_log_sha256':sha},indent=2)+'\n')
 marker='# The shared make check-unix target also starts'
 assert recipe.count(marker)==1
 subprocess.run(['bash','-euo','pipefail','-c','cd /build/compile\n'+recipe[recipe.index(marker):]],check=True)
 assert hashlib.sha256(crypto.read_bytes()).hexdigest()==sha
 after=artifacts();assert all(after[k]==v for k,v in before.items())
 (w/'finish-2-retained.json').write_text(json.dumps({'original_ELFs_unchanged':len(before),'crypto_log_unchanged':True,'new_ELFs':sorted(after.keys()-before.keys())},indent=2)+'\n')
