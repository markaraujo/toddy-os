"""Real Enchant Aspell provider, private UTF8 personal state, CLI and recovery."""
from pathlib import Path
import ctypes,hashlib,json,os,subprocess,sys
root=Path(sys.argv[1]);work=Path(sys.argv[2]);work.mkdir(mode=0o700)
os.environ.update(HOME=str(work),XDG_CONFIG_HOME=str(work/'config'),XDG_CACHE_HOME=str(work/'cache'))
P=ctypes.c_void_p;S=ctypes.c_char_p;I=ctypes.c_int;N=ctypes.c_ssize_t;V=ctypes.c_size_t;SS=ctypes.POINTER(S)
lib=ctypes.CDLL(str(root/'usr/lib/libenchant-2.so.2'))
for name,args,result in [('enchant_broker_init',[],P),('enchant_broker_free',[P],None),('enchant_broker_set_ordering',[P,S,S],None),('enchant_broker_request_dict',[P,S],P),('enchant_broker_free_dict',[P,P],None),('enchant_dict_check',[P,S,N],I),('enchant_dict_add',[P,S,N],None),('enchant_dict_add_to_session',[P,S,N],None),('enchant_dict_remove_from_session',[P,S,N],None),('enchant_dict_suggest',[P,S,N,ctypes.POINTER(V)],SS),('enchant_dict_free_string_list',[P,SS],None)]:
 f=getattr(lib,name);f.argtypes=args;f.restype=result
DESCRIBE=ctypes.CFUNCTYPE(None,S,S,S,S,P)
lib.enchant_dict_describe.argtypes=[P,DESCRIBE,P];lib.enchant_dict_describe.restype=None

def open_dict():
 b=lib.enchant_broker_init();assert b
 lib.enchant_broker_set_ordering(b,b'en_US',b'aspell')
 d=lib.enchant_broker_request_dict(b,b'en_US');assert d
 return b,d
def close(b,d):lib.enchant_broker_free_dict(b,d);lib.enchant_broker_free(b)
def check(d,w):return lib.enchant_dict_check(d,w.encode(),-1)
def state():return {str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*') if p.is_file()}
b,d=open_dict();description=[]
@DESCRIBE
def describe(language,provider,details,file,data):description.append([v.decode() for v in [language,provider,details,file]])
lib.enchant_dict_describe(d,describe,None);assert len(description)==1 and description[0][1].casefold()=='aspell'
assert check(d,'hello')==0 and check(d,'world')==0 and check(d,'helllo')==1
count=V();words=lib.enchant_dict_suggest(d,b'helllo',-1,ctypes.byref(count));assert words and count.value>0
suggestions=[words[i].decode() for i in range(count.value)];lib.enchant_dict_free_string_list(d,words);assert 'hello' in suggestions
personal='toddyaçãozzqv';session='toddyzzqvsession';assert check(d,personal)==1
lib.enchant_dict_add(d,personal.encode(),-1);assert check(d,personal)==0;close(b,d)
saved=state();assert saved
for cycle in range(2):
 b,d=open_dict();assert check(d,personal)==0 and check(d,session)==1
 lib.enchant_dict_add_to_session(d,session.encode(),-1);assert check(d,session)==0
 lib.enchant_dict_remove_from_session(d,session.encode(),-1);assert check(d,session)==1
 assert not lib.enchant_broker_request_dict(b,b'zz_TODDY_UNKNOWN')
 assert lib.enchant_dict_check(d,b'\xff\xfe',2)==-1
 assert check(d,'hello')==0 and check(d,personal)==0
 close(b,d);assert state()==saved
cli=[str(root/'usr/bin/enchant-2'),'-d','en_US'];env=dict(os.environ);env['LD_LIBRARY_PATH']=str(root/'usr/lib')
r=subprocess.run(cli+['-l'],input='hello\nhelllo\n',env=env,text=True,capture_output=True,timeout=10)
assert r.returncode==0 and r.stdout.splitlines()==['helllo'],r
bad=subprocess.run(cli+['--toddy-unknown-option'],env=env,text=True,capture_output=True,timeout=10);assert bad.returncode!=0 and state()==saved
print(json.dumps({'provider':'aspell','dictionary':'en_US','known_words':2,'misspelling_and_hello_suggestion':True,'UTF8_personal_persistence':True,'session_add_remove_cycles':2,'unknown_dictionary_and_invalid_UTF8_refusals':4,'user_state_unchanged_on_refusal':True,'recovery_cycles':2,'CLI_list_and_unknown_option':True,'editor_or_GUI_tested':False}))
