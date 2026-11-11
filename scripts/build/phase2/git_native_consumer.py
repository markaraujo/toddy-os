"""Actual offline native Git behavior; identities and content are local fixtures."""
from pathlib import Path
import json,os,subprocess,sys
assert os.getuid()==101 and len(sys.argv)==2
home=Path(sys.argv[1]);os.chdir(home);env={'HOME':str(home),'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'credential.helper','GIT_CONFIG_VALUE_0':'','GIT_TERMINAL_PROMPT':'0','GIT_ASKPASS':'false'}
runs=[]
def git(*args,fail=False,input=None):
 r=subprocess.run(['git',*args],env=env,capture_output=True,text=True,input=input,timeout=20);runs.append({'args':list(args),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 assert (r.returncode!=0) if fail else r.returncode==0,(args,r.stdout,r.stderr)
 return r
assert git('--version').stdout.strip()=='git version 2.55.0'
git('init','--initial-branch=main','repository');os.chdir(home/'repository');git('config','user.name','Toddy native fixture');git('config','user.email','fixture@example.invalid')
Path('proof.txt').write_text('base\n');git('add','proof.txt');git('commit','-m','Local fixture base');base=git('rev-parse','HEAD').stdout.strip()
git('switch','-c','feature');Path('proof.txt').write_text('feature\n');git('commit','-am','Local fixture feature');feature=git('rev-parse','HEAD').stdout.strip()
git('switch','main');git('merge','--ff-only','feature');assert git('rev-parse','HEAD').stdout.strip()==feature and Path('proof.txt').read_text()=='feature\n'
Path('proof.txt').write_text('unsaved local work\n');denied=git('checkout',base,fail=True);assert 'would be overwritten' in denied.stderr and Path('proof.txt').read_text()=='unsaved local work\n' and git('rev-parse','HEAD').stdout.strip()==feature
git('restore','proof.txt');git('fsck','--full','--strict');os.chdir(home);git('clone','--no-hardlinks',str(home/'repository'),'clone');os.chdir(home/'clone');assert git('rev-parse','HEAD').stdout.strip()==feature and Path('proof.txt').read_text()=='feature\n'
credential=git('credential','fill',fail=True,input='protocol=https\nhost=example.invalid\n\n');assert credential.stdout=='' and 'terminal prompts disabled' in credential.stderr
status=dict(l.split(':',1) for l in Path('/proc/self/status').read_text().splitlines() if ':' in l);assert int(status['CapEff'].strip(),16)==0 and status['NoNewPrivs'].strip()=='1'
print(json.dumps({'version':'2.55.0','uid':os.getuid(),'NoNewPrivs':1,'effective_capabilities':0,'local_commit_branch_fastforward_clone_fsck':True,'dirty_checkout_refused_and_content_preserved':True,'credential_missing_prompt_refused':True,'runs':runs}))
