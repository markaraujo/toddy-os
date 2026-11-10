"""Real EditorConfig C API/CLI, layered UTF8 settings and error recovery."""
from pathlib import Path
import ctypes,hashlib,json,os,subprocess,sys
root=Path(sys.argv[1]);w=Path(sys.argv[2]);w.mkdir(mode=0o700)
lib=ctypes.CDLL(str(root/'usr/lib/libeditorconfig.so'))
P=ctypes.c_void_p;S=ctypes.c_char_p;I=ctypes.c_int
for name,args,result in [('editorconfig_handle_init',[],P),('editorconfig_handle_destroy',[P],I),('editorconfig_parse',[S,P],I),('editorconfig_handle_get_name_value_count',[P],I),('editorconfig_handle_get_name_value',[P,I,ctypes.POINTER(S),ctypes.POINTER(S)],None)]:
 f=getattr(lib,name);f.argtypes=args;f.restype=result
parent=w/'projeto-ação';parent.mkdir();child=parent/'src';child.mkdir()
config=parent/'.editorconfig';config.write_text('root = true\n[*]\nindent_style = space\nindent_size = 4\ncharset = utf-8\nend_of_line = lf\ninsert_final_newline = true\n')
(child/'.editorconfig').write_text('[*.py]\nindent_size = 2\n')
file=child/'olá.py';file.write_text('print("Olá Toddy")\n')
def state():return {str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob('*') if p.is_file()}
def parse(path):
 h=lib.editorconfig_handle_init();assert h
 try:
  code=lib.editorconfig_parse(os.fsencode(path),h);out={}
  if code==0:
   for n in range(lib.editorconfig_handle_get_name_value_count(h)):
    k=S();v=S();lib.editorconfig_handle_get_name_value(h,n,ctypes.byref(k),ctypes.byref(v));out[k.value.decode()]=v.value.decode()
  return code,out
 finally:assert lib.editorconfig_handle_destroy(h)==0
before=state();expected={'indent_style':'space','indent_size':'2','tab_width':'2','charset':'utf-8','end_of_line':'lf','insert_final_newline':'true'}
for cycle in range(2):
 code,actual=parse(str(file));assert code==0 and actual==expected,actual
 assert parse('relative.py')[0]==-2
 assert parse(str(file))[1]==expected
assert state()==before
cli=[str(root/'usr/bin/editorconfig'),str(file)];env=dict(os.environ,LD_LIBRARY_PATH=str(root/'usr/lib'))
r=subprocess.run(cli,env=env,text=True,capture_output=True,timeout=10);assert r.returncode==0
assert dict(x.split('=',1) for x in r.stdout.splitlines())==expected
bad=w/'malformed';bad.mkdir();(bad/'.editorconfig').write_text('root=true\n[broken\nindent_size=2\n');(bad/'x').write_text('x\n');badbefore=state()
assert parse(str(bad/'x'))[0]>0
assert state()==badbefore and parse(str(file))[1]==expected
print(json.dumps({'C_API_and_CLI':True,'UTF8_paths_and_layered_settings':True,'properties':expected,'relative_path_and_malformed_config_refusals':2,'input_state_unchanged':True,'recovery_cycles':2,'graphical_editor_tested':False}))
