#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)]
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','toddy-terminal'],text=True)=='install ok installed 0.2.0-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
source=Path('/opt/toddy-build/scripts/build/phase2/toddy-terminal.sh')
assert source.read_bytes()==(T/'usr/share/toddy-terminal/bashrc').read_bytes()
cases=[
 ('new-user',None,{},'[[ $PS1 == *"38;2;69;121;166m"* && $PS1 == *"\\w"* ]]'),
 ('custom-prompt','custom> ',{},'[[ $PS1 == "custom> " ]]'),
 ('opt-out',None,{'TODDY_TERMINAL_PROMPT':'0'},'[[ $PS1 == "\\s-\\v\\$ " ]]'),
 ('plain-terminal',None,{'TERM':'dumb'},'[[ $PS1 == "\\u@\\h \\w \\$ " ]]'),
 ('readonly-stock',None,{},'[[ $PS1 == "\\s-\\v\\$ " ]]'),
]
rows=[]
with tempfile.TemporaryDirectory(prefix='toddy-terminal-check-',dir=T/'var/tmp') as d:
 home=Path(d);os.chown(home,101,101);virtual='/var/tmp/'+home.name
 base=['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T),'/usr/bin/bash']
 for name,ps1,extra,check in cases:
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':virtual,'TERM':'xterm-256color','COLORTERM':'truecolor',**extra}
  if ps1 is not None:env['PS1']=ps1
  start='readonly PS1; ' if name=='readonly-stock' else ''
  code=start+'PROMPT_COMMAND="true"; before=$-; . /etc/skel/.bashrc; first=$PS1; . /etc/skel/.bashrc; [[ $PS1 == "$first" && $PROMPT_COMMAND == true && $- == "$before" ]] && '+check
  r=subprocess.run(base+['--noprofile','--norc','-i','-c',code],env=env,capture_output=True,text=True,timeout=15)
  rows.append({'name':name,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
  assert r.returncode==0 and not r.stdout,(name,r.returncode,r.stdout,r.stderr)
 import shutil
 for n in ['.bashrc','.bash_profile']:shutil.copyfile(T/'etc/skel'/n,home/n)
 login_env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':virtual,'TERM':'xterm-256color','COLORTERM':'truecolor'}
 login=subprocess.run(base+['--login','-i','-c','[[ $PS1 == *"38;2;69;121;166m"* ]]'],env=login_env,capture_output=True,text=True,timeout=15)
 assert login.returncode==0 and not login.stdout,(login.returncode,login.stdout,login.stderr)
 rows.append({'name':'new-user-login-template','exit':login.returncode,'stderr':login.stderr})
 r=subprocess.run(base+['--noprofile','--norc','-c','PS1="unchanged"; . /etc/skel/.bashrc; [[ $PS1 == unchanged ]]'],env=env,capture_output=True,text=True,timeout=15)
 assert r.returncode==0 and not r.stdout and not r.stderr
 rows.append({'name':'noninteractive-silent','exit':r.returncode})
record=json.loads(Path('/var/log/toddy/packages/toddy-terminal_0.2.0-1+toddy1_all.json').read_text())
assert record['installed'] and not record['sources']
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Conffiles}','toddy-terminal'],text=True).strip().startswith('/etc/skel/.bashrc ')
Path('/var/log/toddy/phase2/terminal-defaults-installed-consumer.json').write_text(json.dumps({'scope':'Owned lightweight Bash defaults: actual UID101/NNP new-user/custom/opt-out/plain/readonly/idempotent/hook-preservation and silent noninteractive cases. Existing homes untouched. Actual graphical Terminal rendering remains pending.','runs':rows,'hook_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'no_extra_runtime_tools':True},indent=2)+'\n')
PY
