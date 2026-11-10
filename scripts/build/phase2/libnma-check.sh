#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libnma'],text=True)=='install ok installed 1.10.6-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=Path('/mnt/lfs/sources/phase2/work/libnma-1');expected=json.loads((w/'stage-results.json').read_text())['consumers'];assert not Path('/mnt/lfs/stage').exists();records=[]
for major in [3,4]:
 library='nma' if major==3 else 'nma-gtk4';namespace='NMA' if major==3 else 'NMA4'
 assert subprocess.check_output(prefix+['pkg-config','--modversion','lib'+library],text=True).strip()=='1.10.6'
 with tempfile.TemporaryDirectory(prefix='toddy-NMA-',dir='/mnt/lfs/tmp') as directory:
  p=Path(directory);p.chmod(0o755);original=w/('native-probe-'+str(major));shutil.copyfile(original,p/'probe');(p/'probe').chmod(0o755)
  assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256(original.read_bytes()).digest()
  native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'lib'+library+'.so.0 => /usr/lib/lib'+library+'.so.0' in libs
  assert 'libgcr-4.so.4' in libs and 'libgck-2.so.2' in libs
  actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101','/mnt/lfs',native],env=env,text=True,timeout=20));assert actual==expected[str(major)]
 code="""import gi,json
namespace=NAMESPACE;major=MAJOR
gi.require_version('Gtk',str(major)+'.0');gi.require_version(namespace,'1.0')
from gi.repository import Gtk,GObject
module=__import__('gi.repository',fromlist=[namespace]).__dict__[namespace]
assert Gtk.get_major_version()==major
assert GObject.type_is_a(module.WifiDialog.__gtype__,Gtk.Dialog.__gtype__)
assert GObject.type_is_a(module.CertChooser.__gtype__,Gtk.Widget.__gtype__)
assert module.MobileProvidersDatabase.__gtype__
print(json.dumps({'namespace':namespace+'1.0','GTK_major':major,'public_widget_and_mobile_types':True,'actual_widget_open_tested':False}))
""".replace('NAMESPACE',repr(namespace)).replace('MAJOR',str(major))
 gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=20));records.append({'C':actual,'GI':gi})
Path('/var/log/toddy/phase2/libnma-installed-consumer.json').write_text(json.dumps({'scope':'Owned GTK3+4/Gcr4 library/public selected GI type imports/C ABI/libnm refusal/recovery/SDK only. Source GIR warnings and untested bindings retained; no full namespace conformance. Shared schema cache/actual widget open/focus/credentials/WiFi/network/GNOME pending.','records':records,'loaded_owned_libraries':True},indent=2)+'\n')
PY
