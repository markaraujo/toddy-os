#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2');version='153.7.0esr-1+toddy1'
r=json.loads(Path('/var/log/toddy/packages','firefox_'+version+'_amd64.json').read_text());assert r['installed']
for name,row in r['payload'].items():
 p=T/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),name
 if 'sha256' in row:
  with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],name
 elif 'symlink' in row:assert os.readlink(p)==row['symlink'],name
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','firefox'],text=True)=='install ok installed '+version
assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip()
subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
prefix=['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T)]
env={'PATH':'/usr/bin:/usr/sbin','HOME':'/tmp','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
result=subprocess.run(prefix+['firefox','--version'],env=env,text=True,capture_output=True,timeout=30)
assert result.returncode==0 and '153.7.0' in result.stdout,(result.returncode,result.stdout,result.stderr)
code="""import gi,json
gi.require_version('Gio','2.0')
from gi.repository import Gio
app=Gio.DesktopAppInfo.new_from_filename('/usr/share/applications/firefox.desktop')
assert app and app.get_executable()=='firefox' and app.supports_uris()
print(json.dumps({'name':app.get_name(),'executable':app.get_executable(),'supports_uris':app.supports_uris()}))
"""
app=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=30))
assert (T/'usr/bin/firefox').readlink()==Path('../lib/firefox/firefox')
(L/'firefox-installed-check-1.json').write_text(json.dumps({'scope':'Owned installed payload/dependency integrity, actual UID101/NNP version and native desktop-entry consumer only; normal-owner GUI/content sandbox/TLS/offline/restart still pending','payload_entries':len(r['payload']),'archive_sha256':r['archive_sha256'],'unprivileged_version':{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr},'desktop':app},indent=2)+'\n')
PY
