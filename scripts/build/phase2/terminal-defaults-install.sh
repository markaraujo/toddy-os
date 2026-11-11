#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path('/opt/toddy-build');T=Path('/mnt/lfs')
stage=T/'sources/stage/phase2-toddy-terminal'
assert not stage.exists(),'Inspect native transaction and package before replay'
for name in ['etc/skel/.bashrc','etc/skel/.bash_profile','usr/share/toddy-terminal/bashrc']:
 assert not (T/name).exists() and not (T/name).is_symlink(),name
assert shutil.disk_usage(T).free>=16*1024**3+2*1024**2
(stage/'etc/skel').mkdir(parents=True)
(stage/'usr/share/toddy-terminal').mkdir(parents=True)
doc=stage/'usr/share/doc/toddy-terminal';doc.mkdir(parents=True)
hook=root/'scripts/build/phase2/toddy-terminal.sh'
shutil.copyfile(hook,stage/'usr/share/toddy-terminal/bashrc')
(stage/'etc/skel/.bashrc').write_text('# Toddy OS Bash defaults; personalize this file freely.\nif [ -r /usr/share/toddy-terminal/bashrc ]; then\n    . /usr/share/toddy-terminal/bashrc\nfi\n')
(stage/'etc/skel/.bash_profile').write_text('# Toddy OS Bash login defaults; personalize freely.\nif [ -r \"$HOME/.bashrc\" ]; then\n    . \"$HOME/.bashrc\"\nfi\n')
shutil.copyfile(root/'LICENSE',doc/'copyright')
shutil.copyfile(root/'LICENSES/CC-BY-4.0.txt',doc/'CC-BY-4.0.txt')
(doc/'README').write_text('Toddy terminal defaults\n\nNew Bash users receive a quiet username/host/path prompt. The navy accent\nis used only on true-color terminals. Custom prompts, fonts, hooks and\nexisting home files are preserved.\n\nSet TODDY_TERMINAL_PROMPT=0 before sourcing your .bashrc to opt out.\nExisting users can add this line after their own settings if desired:\n    . /usr/share/toddy-terminal/bashrc\n\nThis README is CC BY 4.0; original shell code is MIT. Full texts accompany\nthis package. Source is retained in the versioned Toddy OS build recipes.\n')
for p in stage.rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
subprocess.run(['python3',str(root/'scripts/build/stage_package.py'),'toddy-terminal','0.2.0-1+toddy1',str(stage),'--architecture','all','--recipe','scripts/build/phase2/terminal-defaults-install.sh','--depends','bash (>= 5.3-1)','--conffile','/etc/skel/.bashrc','--conffile','/etc/skel/.bash_profile','--install'],cwd=root,check=True)
Path('/var/log/toddy/phase2/terminal-defaults-source.json').write_text(json.dumps({'hook_sha256':hashlib.sha256(hook.read_bytes()).hexdigest(),'scope':'Original MIT/versioned recipe defaults and new-user skeleton only; no existing home/profile/font/hook modified'},indent=2)+'\n')
PY
