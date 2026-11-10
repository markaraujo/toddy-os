#!/usr/bin/env python3
"""Transfer measured native acceptance only after actual child and parent checks."""
from pathlib import Path
import hashlib,json,shlex,subprocess
import phase2_vm
C=phase2_vm.ROOT/'.local/phase2/native-login-policy-runtime-1'
r=json.loads((C/'result.json').read_text());report=json.loads((C/'native-report.json').read_text())
assert r['phase']=='native-report-recorded' and r['backing_unchanged'] and r['native_selected_passed'] and r['summary']['all_selected_exits_zero']
s=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',r['container_id']],text=True));assert not s['Running'] and not s['OOMKilled'] and s['ExitCode']==0
assert len(report['runs'])==15 and all(p['exit']==0 for p in report['runs']) and len(report['session_cycles'])==2
assert report['ephemeral_user_removed'] and report['existing_PAM_and_module_artifacts_unchanged']==14
assert report['session_cycles'][0]['bus_id_sha256']!=report['session_cycles'][1]['bus_id_sha256']
assert r['builder_recovery']['ephemeral_native_user_absent_in_parent'] and r['builder_recovery']['restored_volumes']==6
accepted={'scope':'Measured installed login PAM policy native acceptance only, not GDM/greeter/GNOME/physical acceptance','input_commit':r['commit'],'summary':r['summary'],'native_probe_sha256':r['probe_sha256'],'fixture_manifest_sha256':report['fixture_manifest_sha256'],'native_container_id':r['container_id'],'native_container_exit':s['ExitCode'],'native_container_OOM':s['OOMKilled'],'report':report,'parent_recovery':r['builder_recovery']}
code=r'''from pathlib import Path
import fcntl,hashlib,json,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from schema_union_install import verify
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
a=ACCEPTED
p=Path('/mnt/lfs/sources/phase2/native-fixtures/login-policy-1/accepted.json');assert hashlib.sha256(p.read_bytes()).hexdigest()==a['fixture_manifest_sha256']
fixture=json.loads(p.read_text())
for n,sha in fixture['installed_artifacts'].items():assert hashlib.sha256((Path('/mnt/lfs')/n.lstrip('/')).read_bytes()).hexdigest()==sha
verify(json.loads(Path('/var/log/toddy/packages/toddy-login-policy_0.1.0-1+toddy1_all.json').read_text()))
a['policy_sha256']=fixture['policy_sha256'];a['installed_artifacts']=fixture['installed_artifacts']
p=Path('/var/log/toddy/phase2/login-policy-native-accepted-1.json');data=json.dumps(a,indent=2)+'\n'
if p.exists():assert p.read_text()==data,'Reconcile existing acceptance receipt, no overwrite'
else:p.write_text(data)
print(json.dumps({'native_acceptance':'measured actual15outcomes/two native sessions','report_sha256':a['summary']['report_sha256'],'parent_artifacts_unchanged':len(fixture['installed_artifacts'])}))
'''.replace('ACCEPTED',repr(accepted))
v=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=30);print(v.stdout);print(v.stderr);assert v.returncode==0
