"""Real Aspell C API/CLI with shipped dictionary and private persistent state."""
from pathlib import Path
import ctypes,hashlib,json,os,re,subprocess,sys
root=Path(sys.argv[1]);work=Path(sys.argv[2]);work.mkdir(mode=0o700)
dictionaries=root/'usr/lib/aspell-0.60'
lib=ctypes.CDLL(str(root/'usr/lib/libaspell.so.15'))
P=ctypes.c_void_p;S=ctypes.c_char_p;I=ctypes.c_int
for name,args,result in [('new_aspell_config',[],P),('delete_aspell_config',[P],None),('aspell_config_replace',[P,S,S],I),('new_aspell_speller',[P],P),('aspell_error_number',[P],ctypes.c_uint),('aspell_error_message',[P],S),('delete_aspell_can_have_error',[P],None),('to_aspell_speller',[P],P),('delete_aspell_speller',[P],None),('aspell_speller_check',[P,S,I],I),('aspell_speller_add_to_personal',[P,S,I],I),('aspell_speller_add_to_session',[P,S,I],I),('aspell_speller_clear_session',[P],I),('aspell_speller_save_all_word_lists',[P],I),('aspell_speller_suggest',[P,S,I],P),('aspell_word_list_elements',[P],P),('aspell_string_enumeration_next',[P],S),('delete_aspell_string_enumeration',[P],None)]:
 f=getattr(lib,name);f.argtypes=args;f.restype=result
personal=work/'owner.pws';replacement=work/'owner.prepl'
def config(**extra):
 c=lib.new_aspell_config();assert c
 values={'lang':'en_US','encoding':'utf-8','dict-dir':str(dictionaries),'data-dir':str(dictionaries),'personal':str(personal),'repl':str(replacement)};values.update(extra)
 for key,value in values.items():assert lib.aspell_config_replace(c,key.encode(),value.encode())==1,key
 return c
def speller(**extra):
 c=config(**extra);e=lib.new_aspell_speller(c);lib.delete_aspell_config(c);assert e
 error=lib.aspell_error_number(e)
 if error:
  message=lib.aspell_error_message(e).decode();lib.delete_aspell_can_have_error(e);raise AssertionError(message)
 return lib.to_aspell_speller(e)
def check(s,word):return lib.aspell_speller_check(s,word.encode(),-1)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
personal_word='toddyaçãozzqv';session_word='toddyzzqvsession'
s=speller();assert check(s,'hello')==1 and check(s,'world')==1 and check(s,'helllo')==0
words=lib.aspell_speller_suggest(s,b'helllo',-1);assert words
iterator=lib.aspell_word_list_elements(words);suggestions=[]
while word:=lib.aspell_string_enumeration_next(iterator):suggestions.append(word.decode('utf-8'))
lib.delete_aspell_string_enumeration(iterator);assert 'hello' in suggestions
assert check(s,personal_word)==0
assert lib.aspell_speller_add_to_personal(s,personal_word.encode(),-1)==1
assert lib.aspell_speller_save_all_word_lists(s)==1 and check(s,personal_word)==1
lib.delete_aspell_speller(s);assert personal.is_file();saved=digest(personal)
for cycle in range(2):
 s=speller();assert check(s,personal_word)==1 and check(s,session_word)==0
 assert lib.aspell_speller_add_to_session(s,session_word.encode(),-1)==1 and check(s,session_word)==1
 assert lib.aspell_speller_clear_session(s)==1 and check(s,session_word)==0
 lib.delete_aspell_speller(s)
 assert digest(personal)==saved
corrupt=work/'invalid.rws';corrupt.write_bytes(b'not an aspell dictionary\n');corrupt_hash=digest(corrupt)
for extra in [{'lang':'zz_TODDY_UNKNOWN'},{'master':str(corrupt)}]:
 c=config(**extra);e=lib.new_aspell_speller(c);lib.delete_aspell_config(c)
 assert e and lib.aspell_error_number(e)!=0
 lib.delete_aspell_can_have_error(e)
 assert digest(corrupt)==corrupt_hash and digest(personal)==saved
 s=speller();assert check(s,'hello')==1 and check(s,personal_word)==1;lib.delete_aspell_speller(s)
c=config();assert lib.aspell_config_replace(c,b'toddy-unknown-option',b'true')==0;lib.delete_aspell_config(c)
cli=[str(root/'usr/bin/aspell'),'--lang=en_US','--encoding=utf-8','--dict-dir='+str(dictionaries),'--data-dir='+str(dictionaries),'--personal='+str(personal),'--repl='+str(replacement)]
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(root/'usr/lib')
r=subprocess.run(cli+['-a'],input='hello\nhelllo\n',env=env,capture_output=True,text=True,timeout=10)
assert r.returncode==0 and re.search(r'^\*$',r.stdout,re.M) and re.search(r'^[&#] helllo',r.stdout,re.M),r
bad=subprocess.run(cli+['--toddy-unknown-option'],env=env,capture_output=True,text=True,timeout=10);assert bad.returncode!=0 and digest(personal)==saved
print(json.dumps({'dictionary':'en_US official SCOWL2020.12.07','API_known_words':2,'misspelling_and_hello_suggestion':True,'UTF8_personal_word_persistence':True,'session_add_clear_cycles':2,'invalid_language_dictionary_option_refusals':3,'malformed_dictionary_unchanged':True,'personal_file_unchanged_on_refusal':True,'recovery_cycles':2,'CLI_pipe_and_unknown_option':True,'graphical_or_Portuguese_dictionary_tested':False}))
