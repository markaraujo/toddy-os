#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');stage=T/'sources/stage/phase2-toddy-desktop-audio'
assert not stage.exists() and not stage.is_symlink(),'Inspect actual package/stage before retry'
assert shutil.disk_usage(T).free>=16*1024**3+2*1024**2
links={'default.target.wants/pipewire.service':'pipewire.service','default.target.wants/pipewire-pulse.service':'pipewire-pulse.service','sockets.target.wants/pipewire.socket':'pipewire.socket','sockets.target.wants/pipewire-pulse.socket':'pipewire-pulse.socket','pipewire.service.wants/wireplumber.service':'wireplumber.service','pipewire-session-manager.service':'wireplumber.service'}
providers={}
for name,version in [('pipewire','1.6.8-1+toddy1'),('wireplumber','0.5.15-1+toddy1')]:
 assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',name],text=True)==version
 r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert r['installed'];providers[name]={'version':version,'archive_sha256':r['archive_sha256']}
 for unit in set(links.values()):
  path='/usr/lib/systemd/user/'+unit
  if path in r['payload']:assert hashlib.sha256((T/path.lstrip('/')).read_bytes()).hexdigest()==r['payload'][path]['sha256']
for suffix,unit in links.items():
 name='etc/systemd/user/'+suffix
 assert not os.path.lexists(T/name),'Preserve existing session audio selection'
 assert (T/'usr/lib/systemd/user'/unit).is_file()
 p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to('/usr/lib/systemd/user/'+unit)
doc=stage/'usr/share/doc/toddy-desktop-audio';doc.mkdir(parents=True)
shutil.copyfile(R/'LICENSE',doc/'copyright');shutil.copyfile(R/'LICENSES/CC-BY-4.0.txt',doc/'CC-BY-4.0.txt')
(doc/'README').write_text('''Toddy desktop session audio

Owned standard systemd user enablement links start installed PipeWire, its Pulse
compatibility sockets and WirePlumber for ordinary user sessions. Upstream units,
security restrictions and ConditionUser=!root are unchanged. No host service,
root audio daemon, existing user profile, device permission or audio group is
changed. Upstream PipeWire Pulse units conflict with the standalone Pulse daemon.
Pulse libraries/tools remain installed for native clients, not a second selected
session server. A per-user systemd override/mask takes priority over these defaults.

These package-owned enablement links are reversible by native package removal.
Do not replay an uncertain transaction: inspect package ownership and actual links.
No speaker/microphone/physical audio acceptance follows from enabling services;
real virtual audio/UI/capture checks are separate. Configuration is MIT and this
README is CC BY4.0. Full texts accompany the package.
''')
for p in stage.rglob('*'):
 if not p.is_symlink():p.chmod(0o755 if p.is_dir() else 0o644)
subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),'toddy-desktop-audio','0.2.0-1+toddy1',str(stage),'--architecture','all','--recipe','scripts/build/phase2/desktop-audio-install.sh','--depends','pipewire (= 1.6.8-1+toddy1), wireplumber (= 0.5.15-1+toddy1)','--install'],cwd=R,check=True)
Path('/var/log/toddy/phase2/desktop-audio-policy.json').write_text(json.dumps({'scope':'Standard owned session-unit enablement only; runtime audio/UI and physical hardware unproven.','providers':providers,'links':links},indent=2)+'\n')
PY
