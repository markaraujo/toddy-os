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
    result={'scope':'Native kernel headless Mutter/Wayland and original '+config.get('component','libadwaita')+' display drivers; no GDM/KMS/full GNOME/product acceptance','display':os.environ['WAYLAND_DISPLAY'],'runs':runs}
    destination=root/'suite-result.json'
    def save():destination.write_text(json.dumps(result,indent=2)+'\n')
    env={**os.environ,'GDK_BACKEND':'wayland','GDK_DISABLE':'vulkan','GSETTINGS_BACKEND':'memory','GTK_A11Y':'test','NO_AT_BRIDGE':'1'}
    try:
        if config['fixture']:
            r=subprocess.run([config['fixture']],cwd=root,env=env,capture_output=True,text=True,timeout=25)
            row={'name':'native-gtk-window','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};runs.append(row)
            if r.returncode==0:
                data=json.loads(r.stdout);assert data['mapped'] and data['wayland'] and data['focus_selected'] and data['clicks']==1
                result['gtk_window']=data
            save()
        deadline=time.monotonic()+300
        for index,test in enumerate(config['tests']):
            test_env={**env,**config['test_env'],'LD_LIBRARY_PATH':config.get('test_library_path','/build/compile/src:/build/stage/usr/lib')}
            if config.get('syntax_only'):
                assert len(config['tests'])==1 and test['name']=='test-syntax'
                layout=root/'syntax-layout';fixture=layout/'testsuite';fixture.mkdir(parents=True)
                (fixture/'data').symlink_to(Path(config['source'])/'data',target_is_directory=True)
                (layout/'tests').symlink_to(Path(config['source'])/'tests',target_is_directory=True)
                test_env['G_TEST_SRCDIR']=str(fixture)
                result['syntax_fixture_layout']={'scope':'Private exact source symlinks compensate original setup_search_paths using G_TEST_SRCDIR/data; no source/test/data changes','source':config['source'],'G_TEST_SRCDIR':str(fixture)}
            args=test['cmd'];assert args[0].startswith(config.get('test_binary_prefix','/build/compile/tests/'))
            assert sha(Path(args[0]))==test['sha256']
            commands=[(case,args+['-p',case]) for case in config['syntax_cases']] if config.get('syntax_cases') else [(None,args)]
            outcomes=[];stdout=[];stderr=[];selected_exit=0
            for case,command in commands:
                try:
                    r=subprocess.run(command,cwd=test.get('workdir') or '/build/compile',env=test_env,capture_output=True,text=True,timeout=max(1,min(test['timeout'],deadline-time.monotonic())))
                    text=r.stdout;lines=re.findall(r'^ok\s+[0-9]+(?:\s+.*)?$',text,re.M)
                    skipped=[s for s in lines if '# SKIP' in s]
                    item={'exit':r.returncode,'passed_case_executions':len(lines)-len(skipped),'skipped_case_executions':len(skipped),'skip_lines':skipped}
                    if test.get('protocol')=='meson':
                        original_results=[json.loads(line) for line in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines() if line.strip()]
                        actual_names=[row['name'].split(':',1)[-1] for row in original_results]
                        item['meson_coverage_complete']=len(actual_names)==len(test['expected_test_names']) and set(actual_names)==set(test['expected_test_names'])
                        item['meson_all_results_ok']=bool(original_results) and all(row['result']=='OK' and row['returncode']==0 for row in original_results)
                        item['meson_original_results']=original_results
                        tap=[line for row in original_results for line in (row.get('stdout') or '').splitlines() if re.match(r'^ok\s+\d+(?:\s|$)',line)]
                        skipped=[line for line in tap if re.search(r'#\s*SKIP\b',line,re.I)]
                        item['passed_case_executions']=len(tap)-len(skipped)
                        item['skipped_case_executions']=len(skipped)
                        item['skip_lines']=skipped
                    if case is not None:
                        item['case']=case
                        assert len(lines)==1 and case in lines[0], 'Selected original case did not execute exactly once'
                    stdout.append(r.stdout);stderr.append(r.stderr)
                except subprocess.TimeoutExpired as error:
                    convert=lambda x:x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
                    item={'exit':None,'timeout':test['timeout']};stdout.append(convert(error.stdout));stderr.append(convert(error.stderr))
                outcomes.append(item)
                if item['exit']!=0:
                    selected_exit=item['exit'];break
            row={'name':test['name'],'exit':selected_exit,'passed_case_executions':sum(x.get('passed_case_executions',0) for x in outcomes),'skipped_case_executions':sum(x.get('skipped_case_executions',0) for x in outcomes),'skip_lines':[s for x in outcomes for s in x.get('skip_lines',[])],'stdout':''.join(stdout),'stderr':''.join(stderr)}
            if test.get('protocol')=='meson':
                assert len(outcomes)==1
                row.update({key:outcomes[0].get(key) for key in ['meson_coverage_complete','meson_all_results_ok','meson_original_results']})
            if config.get('syntax_cases'):row['selected_original_subcases']=outcomes
            runs.append(row);save()
            print('TODDY_NATIVE_WIDGET_PROGRESS',test['name'],row['exit'],flush=True)
            if row['exit'] not in (0,77):
                runs.extend({'name':t['name'],'exit':None,'not_run':'Prior original widget test failed/timed out; preserve and diagnose before more equivalent runs'} for t in config['tests'][index+1:]);save();break
        result['widget_drivers_attempted']=sum(1 for r in runs if r['name']!='native-gtk-window' and 'not_run' not in r)
        result['widget_drivers_exit_zero']=sum(1 for r in runs if r['name']!='native-gtk-window' and r['exit']==0)
        result['passed_case_executions']=sum(r.get('passed_case_executions',0) for r in runs)
        result['skipped_case_executions']=sum(r.get('skipped_case_executions',0) for r in runs)
        result['all_selected_exits_zero']=len(runs)==len(config['tests'])+int(bool(config['fixture'])) and all(r['exit']==0 and r.get('meson_coverage_complete',True) and r.get('meson_all_results_ok',True) for r in runs)
    except Exception as error:
        result['suite_error']={'type':type(error).__name__,'message':str(error)};result['all_selected_exits_zero']=False
    finally:save()
    raise SystemExit(0 if result.get('all_selected_exits_zero') else 1)
if __name__=='__main__':main()
