"""Run actual GTK/Wayland fixture and deferred original Libadwaita drivers."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

CONFIG = None

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert os.getuid()==101 and os.getgid()==101
    assert 'NoNewPrivs:\t1' in Path('/proc/self/status').read_text()
    assert 'CapEff:\t0000000000000000' in Path('/proc/self/status').read_text()
    assert os.environ.get('WAYLAND_DISPLAY') and os.environ.get('DBUS_SESSION_BUS_ADDRESS')
    config=CONFIG;assert isinstance(config,dict);root=Path(config['root']);runs=[]
    result={'scope':'Native kernel headless Mutter/Wayland, actual mapped GTK client fixture and original Libadwaita widget programs; no GDM/KMS/full GNOME/product acceptance','display':os.environ['WAYLAND_DISPLAY'],'runs':runs}
    destination=root/'suite-result.json'
    def save():destination.write_text(json.dumps(result,indent=2)+'\n')
    env={**os.environ,'GDK_BACKEND':'wayland','GDK_DISABLE':'vulkan','GSETTINGS_BACKEND':'memory','GTK_A11Y':'test','NO_AT_BRIDGE':'1'}
    try:
        r=subprocess.run([config['fixture']],cwd=root,env=env,capture_output=True,text=True,timeout=25)
        row={'name':'native-gtk-window','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};runs.append(row)
        if r.returncode==0:
            data=json.loads(r.stdout);assert data['mapped'] and data['wayland'] and data['focus_selected'] and data['clicks']==1
            result['gtk_window']=data
        save()
        deadline=time.monotonic()+300
        for index,test in enumerate(config['tests']):
            test_env={**env,**config['test_env'],'LD_LIBRARY_PATH':'/build/compile/src:/build/stage/usr/lib'}
            args=test['cmd'];assert args[0].startswith('/build/compile/tests/')
            assert sha(Path(args[0]))==test['sha256']
            try:
                r=subprocess.run(args,cwd=test.get('workdir') or '/build/compile',env=test_env,capture_output=True,text=True,timeout=max(1,min(test['timeout'],deadline-time.monotonic())))
                text=r.stdout;lines=re.findall(r'^ok\s+[0-9]+(?:\s+.*)?$',text,re.M)
                skipped=[s for s in lines if '# SKIP' in s]
                row={'name':test['name'],'exit':r.returncode,'passed_case_executions':len(lines)-len(skipped),'skipped_case_executions':len(skipped),'skip_lines':skipped,'stdout':r.stdout,'stderr':r.stderr}
            except subprocess.TimeoutExpired as error:
                convert=lambda x:x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
                row={'name':test['name'],'exit':None,'timeout':test['timeout'],'stdout':convert(error.stdout),'stderr':convert(error.stderr)}
            runs.append(row);save()
            print('TODDY_NATIVE_WIDGET_PROGRESS',test['name'],row['exit'],flush=True)
            if row['exit'] not in (0,77):
                runs.extend({'name':t['name'],'exit':None,'not_run':'Prior original widget test failed/timed out; preserve and diagnose before more equivalent runs'} for t in config['tests'][index+1:]);save();break
        result['widget_drivers_attempted']=sum(1 for r in runs if r['name']!='native-gtk-window' and 'not_run' not in r)
        result['widget_drivers_exit_zero']=sum(1 for r in runs if r['name']!='native-gtk-window' and r['exit']==0)
        result['passed_case_executions']=sum(r.get('passed_case_executions',0) for r in runs)
        result['skipped_case_executions']=sum(r.get('skipped_case_executions',0) for r in runs)
        result['all_selected_exits_zero']=len(runs)==68 and all(r['exit']==0 for r in runs)
    except Exception as error:
        result['suite_error']={'type':type(error).__name__,'message':str(error)};result['all_selected_exits_zero']=False
    finally:save()
    raise SystemExit(0 if result.get('all_selected_exits_zero') else 1)
if __name__=='__main__':main()
