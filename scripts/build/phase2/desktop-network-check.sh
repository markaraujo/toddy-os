#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
root=Path('/mnt/lfs');prefix=['chroot',str(root)]
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','toddy-desktop-network'],text=True)=='install ok installed 0.2.0-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
proof=json.loads(Path('/var/log/toddy/phase2/desktop-network-policy-source.json').read_text())
generator=Path('/opt/toddy-build/scripts/build/phase2/desktop_network.py')
assert hashlib.sha256(generator.read_bytes()).hexdigest()==proof['generator_sha256']
stage=root/'sources/stage/phase2-toddy-desktop-network'
checked=[]
for p in stage.rglob('*'):
    relative=p.relative_to(stage)
    if relative.parts[0]=='DEBIAN' or p.is_dir() and not p.is_symlink():continue
    actual=root/relative
    if p.is_symlink():assert actual.is_symlink() and os.readlink(actual)==os.readlink(p)
    else:
        assert actual.is_file() and not actual.is_symlink() and actual.read_bytes()==p.read_bytes()
        s=actual.stat();assert s.st_uid==s.st_gid==0 and s.st_mode&0o777==0o644
    checked.append(str(relative))
conffiles=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Conffiles}','toddy-desktop-network'],text=True)
assert {line.split()[0] for line in conffiles.splitlines() if line.strip()}==set(proof['conffiles'])
assert (root/'etc/resolv.conf').readlink()==Path('/run/systemd/resolve/stub-resolv.conf')
assert (root/'etc/systemd/system/multi-user.target.wants/systemd-networkd.service').is_symlink()
assert not (root/'etc/systemd/system/network-online.target.wants/NetworkManager-wait-online.service').exists()
conditions=[]
for item in proof['conffiles']:
    if not item.endswith('owner.conf'):continue
    condition=next(l for l in (root/item.lstrip('/')).read_text().splitlines() if l.startswith('ConditionPathExists='))
    p=subprocess.run(prefix+['systemd-analyze','condition',condition],capture_output=True,text=True)
    expected=0 if '/NetworkManager.service.d/' in item else 1
    assert p.returncode==expected,(item,p.returncode,p.stderr)
    conditions.append({'unit_dropin':item,'condition_exit':p.returncode})
denial='''from pathlib import Path
import errno
for name in NAMES:
 try:f=open(name,'r+')
 except OSError as e:assert e.errno in (errno.EACCES,errno.EROFS)
 else:f.close();raise AssertionError('Unprivileged policy write possible')
'''.replace('NAMES',repr(proof['conffiles']))
subprocess.run(['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(root),'python3','-c',denial],check=True)
Path('/var/log/toddy/phase2/desktop-network-policy-check.json').write_text(json.dumps({'scope':'Installed configuration/ownership, inverse native condition evaluation and UID101/NNP write refusal only; no running PID1/daemon/DHCP/DNS/GUI/offline/reboot/recovery acceptance','checked_payload':checked,'conditions':conditions,'unprivileged_policy_write_denied':True},indent=2)+'\n')
PY
