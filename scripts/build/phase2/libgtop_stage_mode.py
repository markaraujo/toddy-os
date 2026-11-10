"""Correct only the uninstalled private helper mode; reuse successful API evidence."""
from pathlib import Path
import hashlib,json,os,stat,subprocess

def main(recipe):
 w=Path('/build');receipt=w/'stage-helper-mode-correction-3.json';assert not receipt.exists() and not (w/'stage-results.json').exists()
 before=json.loads((w/'before-collect-2.json').read_text())
 def files(base,elf=False):
  return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
 assert files(w/'compile',True)==before['artifacts'] and files(Path('/stage'))==before['stage_sha256']
 p=Path('/stage/usr/libexec/libgtop_server2');s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==s.st_gid==101 and s.st_mode&0o7777==0o4755
 assert p.resolve()==p and p.stat().st_dev==w.stat().st_dev
 state={'state':'mode-change-intended','scope':'Only own uninstalled staged helper mode, no root privilege/helper execution/source/compiler/restage or package transaction','path':str(p),'inode':s.st_ino,'uid':s.st_uid,'gid':s.st_gid,'mode_before':oct(s.st_mode&0o7777),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 receipt.write_text(json.dumps(state,indent=2)+'\n');p.chmod(0o755)
 assert p.stat().st_ino==s.st_ino and p.stat().st_uid==101 and p.stat().st_mode&0o7777==0o755
 assert files(w/'compile',True)==before['artifacts'] and files(Path('/stage'))==before['stage_sha256']
 marker="python3 - <<'PY'\nfrom pathlib import Path\nimport hashlib,json,os,stat"
 assert recipe.count(marker)==1
 subprocess.run(['bash','-euo','pipefail','-c',recipe[recipe.index(marker):]],check=True)
 r=json.loads((w/'stage-results.json').read_text());assert r['artifacts']==before['artifacts'] and r['stage_sha256']==before['stage_sha256']
 state.update(state='complete',mode_after='0o755',compiled_and_stage_bytes_unchanged=True,successful_API_log_reused=True);receipt.write_text(json.dumps(state,indent=2)+'\n')
