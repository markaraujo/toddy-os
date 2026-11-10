"""Check private original GSettings environment independently of kernel indexing."""
from pathlib import Path
import ast,hashlib,json,os,subprocess

assert os.getuid()==101
base=Path('/build/settings-diagnosis-1');assert not base.exists();base.mkdir()
root=Path('/build/compile');before={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
worker=r'''from pathlib import Path
import json,os,subprocess
schema='org.freedesktop.Tracker3.Miner.Files';key='index-recursive-directories'
expected=[str(Path.cwd()/'monitored')]
write=subprocess.run(['gsettings','set',schema,key,str(expected)],capture_output=True,text=True)
read=subprocess.run(['gsettings','get',schema,key],capture_output=True,text=True)
print(json.dumps({'write_exit':write.returncode,'write_stderr':write.stderr,'read_exit':read.returncode,'read_stderr':read.stderr,'readback':read.stdout.strip(),'expected':expected}))
'''
rows=[]
for name,extra in [('original-module-override',False),('owned-dconf-extra-module',True)]:
 p=base/name;p.mkdir();(p/'trackertest').write_text('user-db:trackertest\n')
 env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','HOME':str(p),'XDG_CONFIG_HOME':str(p/'config'),'XDG_CACHE_HOME':str(p/'cache'),'XDG_RUNTIME_DIR':str(p/'run'),'DCONF_PROFILE':str(p/'trackertest'),'GIO_MODULE_DIR':'/build/compile/tests/functional-tests/mockvolumemonitor','GSETTINGS_SCHEMA_DIR':'/build/compile/data'}
 (p/'run').mkdir(mode=0o700)
 if extra:env['GIO_EXTRA_MODULES']='/usr/lib/gio/modules'
 result=subprocess.run(['dbus-run-session','--','python3','-B','-c',worker],cwd=p,env=env,capture_output=True,text=True,timeout=20)
 assert result.returncode==0,result.stderr
 r=json.loads(result.stdout);r['name']=name;r['bus_stderr']=result.stderr
 try:r['persisted']=ast.literal_eval(r['readback'])==r['expected']
 except (SyntaxError,ValueError):r['persisted']=False
 rows.append(r)
assert before=={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
report={'scope':'Actual private GSettings/DConf write-read across processes in same built functional fixture GIO module environment. Builder kernel, no native index/search or package acceptance.','kernel':os.uname().release,'runs':rows,'compiled_inputs_unchanged':True}
(base/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
