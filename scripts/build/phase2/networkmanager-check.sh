#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','networkmanager'],text=True)=='install ok installed 1.58.1-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libnm'],text=True).strip()=='1.58.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=Path('/mnt/lfs/sources/phase2/work/networkmanager-1');expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-NM-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);p.chmod(0o755);shutil.copyfile(w/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((w/'native-probe').read_bytes()).digest()
 native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'libnm.so.0 => /usr/lib/libnm.so.0' in libs
 actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101','/mnt/lfs',native],env=env,text=True,timeout=20));assert actual==expected
cli_versions={}
for args in [['NetworkManager','--version'],['nmcli','--version']]:
 value=subprocess.check_output(prefix+args,env=env,text=True).strip();assert value==('ToddyOS' if args[0]=='NetworkManager' else 'nmcli tool, version ToddyOS');cli_versions[args[0]]=value
code="""import gi,json
gi.require_version('NM','1.0')
from gi.repository import NM
c=NM.SimpleConnection.new();s=NM.SettingConnection.new();s.props.id='Rede sintética · Toddy';c.add_setting(s)
assert c.get_id()=='Rede sintética · Toddy'
print(json.dumps({'namespace':'NM1.0','UTF8_setting':True}))
"""
gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=20))
Path('/var/log/toddy/phase2/networkmanager-installed-consumer.json').write_text(json.dumps({'scope':'Owned full daemon/libnm/nmcli/GI1.0 with actual UID101 typed connection/DBus variant/invalid address refusal/recovery/SDK/CLI version. No system bus service startup, network configuration, actual authorization/persistence/Stop/reconnect or GNOME UI acceptance.','consumer':actual,'GI':gi,'upstream_package_and_SDK_version':'1.58.1','CLI_distribution_version':cli_versions,'loaded_owned_library':True},indent=2)+'\n')
PY
