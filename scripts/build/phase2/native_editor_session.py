"""Run the actual installed editor twice with test-only GTK instrumentation."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
root=Path(sys.argv[1]);library=Path(sys.argv[2]);expected_sha=sys.argv[3]
assert os.geteuid()==os.getegid()==101 and str(root).startswith('/tmp/toddy-editor-native-')
assert hashlib.sha256(library.read_bytes()).hexdigest()==expected_sha
file=root/'documento-ação.txt';file.write_text('Olá Toddy\n')
runs=[];report={'scope':'Actual unmodified installed GNOME Text Editor, native Wayland mapped/active windows, direct GTK widget editing and page.save action, normal close/reopen and client renderer screenshots. Test-only LD_PRELOAD driver, not physical input, complete GNOME/login or crash recovery.','runs':runs,'all_selected_exits_zero':False}
try:
 for phase in ['write','reopen']:
  env={**os.environ,'LD_PRELOAD':str(library),'TODDY_EDITOR_TEST_ROOT':str(root),'TODDY_EDITOR_TEST_FILE':str(file),'TODDY_EDITOR_TEST_PHASE':phase,'GDK_BACKEND':'wayland','GDK_DISABLE':'vulkan','GSETTINGS_BACKEND':'memory','GTK_A11Y':'test','NO_AT_BRIDGE':'1'}
  with (root/('editor-'+phase+'.log')).open('xb') as out:
   r=subprocess.run(['/usr/bin/gnome-text-editor','--standalone',str(file)],env=env,cwd=root,stdout=out,stderr=subprocess.STDOUT,timeout=65)
  row={'name':'editor-'+phase,'exit':r.returncode,'log':(root/('editor-'+phase+'.log')).read_text(errors='replace')};runs.append(row)
  assert r.returncode==0
  result=json.loads((root/('editor-'+phase+'-result.json')).read_text());row['actual_UI']=result
  assert all(result[k] is True for k in ['real_editor_window','mapped_wayland','active_window','text_view_focus','saved_UTF8_document'])
  assert result['wide_size'][0]>result['narrow_size'][0]>0
  assert file.read_text()=='Olá Toddy\nLinha salva offline.\n'
 report['document_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();report['all_selected_exits_zero']=len(runs)==2
except Exception as error:
 report['failure']={'type':type(error).__name__,'message':str(error)}
finally:
 (root/'suite-result.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['all_selected_exits_zero'] else 1)
