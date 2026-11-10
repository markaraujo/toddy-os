"""Qualify the actual generated hook correction with intercepted fixture commands."""
from pathlib import Path
import hashlib,json,subprocess

def main(recipe):
 w=Path('/build');fixture=w/'hook-profile-1';assert not fixture.exists();fixture.mkdir()
 source=w/'compile/src/daemon/Makefile';before=source.read_bytes();p=fixture/'Makefile';p.write_bytes(before)
 start="python3 - <<'PY'\nfrom pathlib import Path\np=Path('/build/compile/src/daemon/Makefile')"
 assert recipe.count(start)==1
 code=recipe[recipe.index(start)+len("python3 - <<'PY'\n"):].split('\nPY\n',1)[0]
 assert code.count("Path('/build/compile/src/daemon/Makefile')")==1
 code=code.replace("Path('/build/compile/src/daemon/Makefile')",'Path('+repr(str(p))+')')
 subprocess.run(['python3','-c',code],check=True)
 old=[line.strip()[1:] for line in before.decode().splitlines() if line.startswith('\t-test -n "$(DESTDIR)" || ')]
 new=[line.strip()[1:] for line in p.read_text().splitlines() if line.startswith('\t-test -n "$(DESTDIR)" || ')]
 assert len(old)==len(new)==1
 intercept="chown(){ printf 'chown\\n'; }; chmod(){ printf 'chmod\\n'; }; libexecdir=/usr/libexec; "
 def run(line,dest):
  line=line.replace('$(DESTDIR)','${DESTDIR}').replace('$(libexecdir)','${libexecdir}')
  return subprocess.check_output(['bash','-euo','pipefail','-c',intercept+'DESTDIR='+repr(dest)+'; '+line],text=True)
 assert run(old[0],'/stage')=='chmod\n'
 assert run(new[0],'/stage')=='' and run(new[0],'')=='chown\nchmod\n'
 assert source.read_bytes()==before
 (w/'hook-profile-1.json').write_text(json.dumps({'scope':'Fixture shell commands intercepted as functions, not actual chown/chmod. Exact canonical correction applied to copied actual generated Makefile. Original compiler Makefile unchanged. Not an installed helper/privilege test.','original_nonempty_DESTDIR_chmod_observed':True,'corrected_nonempty_DESTDIR_no_privilege_commands':True,'corrected_empty_DESTDIR_original_commands_preserved':True,'original_Makefile_sha256':hashlib.sha256(before).hexdigest(),'fixture_corrected_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
