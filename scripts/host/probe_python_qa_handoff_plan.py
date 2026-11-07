#!/usr/bin/env python3
"""Read-only installed provenance check for a private Python QA archive plan."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--transaction', action='store_true', help='Also configure a private native dependency closure and verify interrupted transfer')
parser.add_argument('--image-removal', action='store_true', help='Also remove QA through native Dpkg in the private configured image')
options = parser.parse_args()
if options.image_removal:
    options.transaction = True
sources = {name: base64.b64encode((Path('scripts/build') / name).read_bytes()).decode()
           for name in ('package_backend.py', 'h11/python_qa.py', 'python_qa_handoff.py',
                        'stage_package.py', 'python_qa_bundle.py', 'prepare_python_qa.py',
                        'python_qa_transfer.py', 'python_qa_transaction.py',
                        'h11/remove_image_qa.py', 'h11/audit_private_key_material.py')}
script = r'''from pathlib import Path
import base64,copy,hashlib,json,re,shutil,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-python-qa-handoff-',dir=root/'tmp'))
print('PYTHON_QA_HANDOFF_FIXTURE '+str(base),flush=True)
for name,body in SOURCES.items():
 path=base/'scripts/build'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(body))
modules={}
for name,body in SOURCES.items():
 key=name.removesuffix('.py').replace('/','_')
 module=types.ModuleType(key);module.__file__=str(base/'scripts/build'/name)
 sys.modules[key]=module;exec(compile(base64.b64decode(body),module.__file__,'exec'),module.__dict__)
 modules[name]=module
backend=modules['package_backend.py'].PackageBackend(root)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
version,arch,status=backend.run('dpkg-query','-W','-f=${Version}\t${Architecture}\t${Status}','python',capture_output=True,text=True).stdout.split('\t')
assert status=='install ok installed'
record=json.loads((Path('/var/log/toddy/packages')/f'python_{version}_{arch}.json').read_text())
archive=Path('/var/cache/toddy/packages')/f'python_{version}_{arch}.deb'
assert digest(archive)==record['archive_sha256']
before=digest(root/'var/lib/dpkg/status')
try:
 copied=base/'source.deb';shutil.copyfile(archive,copied)
 runtime=base/'runtime';qa=base/'qa'
 backend.run('dpkg-deb','--extract','/'+str(copied.relative_to(root)),'/'+str(runtime.relative_to(root)))
 modules['h11/python_qa.py'].partition(runtime,qa)
 notice=qa/'usr/share/doc/python-test-support/copyright';notice.parent.mkdir(parents=True)
 shutil.copy2(runtime/'usr/share/doc/python/copyright',notice)
 entries=modules['stage_package.py'].payload(qa)
 ownership={}
 for listing in (root/'var/lib/dpkg/info').glob('*.list'):
  for path in listing.read_text().splitlines():ownership.setdefault(path.rstrip('/'),set()).add(listing.stem)
 revision=re.search(r'\+toddy([1-9][0-9]*)$',version)
 successor=(version[:revision.start()]+'+toddy'+str(int(revision[1])+1)) if revision else version+'+toddy1'
 args=types.SimpleNamespace(name='python-test-support',version=successor,architecture=arch,
  depends=modules['python_qa_handoff.py'].qa_dependencies(successor),source=[r['filename'] for r in record['sources']],install=False)
 def prepare():return modules['python_qa_handoff.py'].prepare(backend,root,Path('/var/cache/toddy/packages'),Path('/var/log/toddy/packages'),modules['stage_package.py'].payload(qa),ownership,qa,args)
 plan=prepare();assert plan['transferred_path_count']==5395 and not plan['installation_authorized']
 rejected=[]
 complete_dependencies=args.depends;args.depends=f'python (= {successor})'
 try:prepare()
 except ValueError as error:rejected.append({'case':'missing direct interpreter providers','reason':str(error)})
 else:raise AssertionError('Incomplete direct dependencies accepted')
 args.depends=complete_dependencies
 args.install=True
 try:prepare()
 except ValueError as error:rejected.append({'case':'install flag','reason':str(error)})
 else:raise AssertionError('Install flag accepted')
 args.install=False
 selected=next(path for path in plan['transferred_paths'] if path.endswith('.py'))
 path=qa/selected.lstrip('/');original=path.read_bytes();mtime=path.stat().st_mtime_ns
 path.write_bytes(original+b'\n# private altered fixture\n')
 try:prepare()
 except ValueError as error:rejected.append({'case':'changed staged bytes','reason':str(error)})
 else:raise AssertionError('Changed QA accepted')
 path.write_bytes(original);import os;os.utime(path,ns=(mtime,mtime))
 assert prepare()==plan
 # Prepare actual native private archives and check the whole core/QA bundle.
 # This exercises reusable build/control functions, never the gated release CLI.
 core_record=copy.deepcopy(record);core_record.update(version=successor,installed=False)
 core_record['payload']=modules['stage_package.py'].payload(runtime)
 qa_record=copy.deepcopy(core_record);qa_record.update(name='python-test-support')
 qa_record['payload']=modules['stage_package.py'].payload(qa)
 qa_record['prepared_ownership_handoff']=plan
 old_text=backend.run('dpkg-deb','-f','/'+str(copied.relative_to(root)),capture_output=True,text=True).stdout
 new_text,count=re.subn(r'^Version: .+$','Version: '+successor,old_text,flags=re.M);assert count==1
 (runtime/'DEBIAN').mkdir();(runtime/'DEBIAN/control').write_text(new_text)
 conffiles=sorted(path for path,row in record['payload'].items() if path.startswith('/etc/') and row.get('sha256'))
 if conffiles:(runtime/'DEBIAN/conffiles').write_text('\n'.join(conffiles)+'\n')
 (qa/'DEBIAN').mkdir();(qa/'DEBIAN/control').write_text('Package: python-test-support\nVersion: '+successor+'\nArchitecture: '+arch+'\nMaintainer: Toddy OS Development <noreply@example.invalid>\nDepends: '+args.depends+'\nDescription: Private native Python QA bundle check\n')
 controls=[modules['prepare_python_qa.py'].read_control(backend,copied)]
 for label,stage,candidate in (('core',runtime,core_record),('qa',qa,qa_record)):
  built=base/(base.name+'-'+label+'.deb')
  backend.build(stage,built,threads=2)
  candidate['archive_sha256']=digest(built)
  controls.append(modules['prepare_python_qa.py'].read_control(backend,built))
  extracted=base/('checked-'+label)
  backend.run('dpkg-deb','--extract','/'+str(built.relative_to(root)),'/'+str(extracted.relative_to(root)))
  assert modules['stage_package.py'].payload(extracted)==candidate['payload'],'Actual archive payload differs'
 def check_bundle():return modules['python_qa_bundle.py'].validate(record,core_record,qa_record,donor_record_sha256=plan['predecessor_record_sha256'],controls=controls)
 bundle=check_bundle();assert bundle['transferred_files']==5395 and not bundle['installation_authorized']
 runtime_path='/usr/lib/python3.14/ssl.py';original_entry=core_record['payload'][runtime_path]
 core_record['payload'][runtime_path]=dict(original_entry,sha256='0'*64)
 try:check_bundle()
 except ValueError as error:rejected.append({'case':'changed retained runtime','reason':str(error)})
 else:raise AssertionError('Changed runtime accepted')
 core_record['payload'][runtime_path]=original_entry;assert check_bundle()==bundle
 transaction_result=None
 image_removal_result=None
 if TRANSACTION:
  raw=backend.run('dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\t${Pre-Depends}\n',capture_output=True,text=True).stdout
  installed={}
  for line in raw.splitlines():
   name,version_value,arch_value,status_value,depends,predepends=line.split('\t')
   if status_value=='install ok installed':installed[name]=(version_value,arch_value,depends+','+predepends)
  selected=set();pending=['python','bash','coreutils','filesystem-layout']
  while pending:
   name=pending.pop()
   if name in selected:continue
   selected.add(name)
   for group in installed[name][2].split(','):
    if not group.strip():continue
    alternatives=[re.match(r'\s*([a-z0-9][a-z0-9+.-]*)',part).group(1) for part in group.split('|')]
    actual=next((candidate for candidate in alternatives if candidate in installed),None)
    assert actual is not None,group
    pending.append(actual)
  dependency_cache=base/'dependencies';dependency_cache.mkdir()
  dependency_archives=[]
  for name in sorted(selected):
   ver,architecture,_=installed[name];stem=f'{name}_{ver}_{architecture}'
   source=Path('/var/cache/toddy/packages')/(stem+'.deb')
   provenance=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
   assert provenance['installed'] and digest(source)==provenance['archive_sha256']
   destination=dependency_cache/source.name;shutil.copy2(source,destination)
   assert digest(destination)==provenance['archive_sha256']
   dependency_archives.append(destination)
  target=base/'configured-root';db=target/'var/lib/dpkg';db.mkdir(parents=True);(db/'status').touch()
  native_root='--root=/'+str(target.relative_to(root))
  with (base/'dependency-install.log').open('w') as log:
   backend.run('dpkg',native_root,'--unpack',*('/'+str(path.relative_to(root)) for path in dependency_archives),stdout=log,stderr=subprocess.STDOUT)
   backend.run('dpkg',native_root,'--configure','--pending',stdout=log,stderr=subprocess.STDOUT)
  db_before=digest(db/'status')
  transaction_dir=base/'transaction';transaction_dir.mkdir(mode=0o700)
  journal=transaction_dir/'transaction.json'
  archives=[copied,base/(base.name+'-core.deb'),base/(base.name+'-qa.deb')]
  data=[record,core_record,qa_record]
  def execute(selected_backend=backend,selected_journal=journal):
   return modules['python_qa_transaction.py'].execute(selected_backend,target,data,archives,selected_journal,
     donor_record_sha256=plan['predecessor_record_sha256'])
  class InterruptAfterCore(modules['package_backend.py'].PackageBackend):
   def run(self,program,*arguments,**kwargs):
    result=super().run(program,*arguments,**kwargs)
    if program=='dpkg' and '--install' in arguments and arguments[-1].endswith('-core.deb'):
     raise RuntimeError('Controlled interruption after actual core installation, before journal exit capture')
    return result
  try:execute(InterruptAfterCore(root))
  except RuntimeError as error:
   assert str(error).startswith('Controlled interruption after actual core'),str(error)
  else:raise AssertionError('Controlled transfer interruption was not reached')
  interrupted=json.loads(journal.read_text())
  assert not interrupted['complete'] and interrupted['actions'][-1]['action']=='install_core'
  assert interrupted['actions'][-1]['exit'] is None
  current=backend.run('dpkg-query','--admindir=/'+str(db.relative_to(root)),'-W','-f=${Version}\t${Status}','python',capture_output=True,text=True).stdout
  assert current==successor+'\tinstall ok installed',current
  try:execute(selected_journal=transaction_dir/'unrecorded.json')
  except ValueError as error:rejected.append({'case':'unrecorded partial installed transfer','reason':str(error)})
  else:raise AssertionError('Unrecorded installed transfer accepted')
  recovered=execute();assert recovered['complete']
  after=digest(db/'status');replayed=execute()
  assert len(replayed['actions'])==len(recovered['actions']) and digest(db/'status')==after
  transaction_result={'dependency_packages':sorted(selected),'dependency_archive_bytes':sum(p.stat().st_size for p in dependency_archives),
    'native_dependency_install_log':(base/'dependency-install.log').read_text(),
    'durable_transaction':replayed,
    'native_action_logs':{path.name:path.read_text() for path in sorted(transaction_dir.glob('action-*.log'))},
    'controlled_interruption_after_real_core_configuration':True,'missing_transaction_rejected':True,
    'complete':recovered['complete'],'verification':recovered['verification'],
    'actions':[{key:value for key,value in step.items() if key in ('action','exit')} for step in recovered['actions']],
    'idempotent_repeat_added_no_native_actions':True,'idempotent_repeat_package_status_unchanged':True}
  if IMAGE_REMOVAL:
   remover=modules['h11/remove_image_qa.py'].remove_image_qa
   audit_keys=modules['h11/audit_private_key_material.py'].scan
   evidence=base/'image-removal';evidence.mkdir(mode=0o700)
   initial_keys=audit_keys(target)
   qa_key_findings=[row for row in initial_keys['findings'] if modules['python_qa_handoff.py'].is_qa(row['path'])]
   other_key_findings=[row for row in initial_keys['findings'] if not modules['python_qa_handoff.py'].is_qa(row['path'])]
   assert len(qa_key_findings)==15,initial_keys
   image_status=digest(db/'status')
   def refused(label,selected_image=target,selected_core=core_record,selected_qa=qa_record):
    try:remover(backend,selected_image,selected_core,selected_qa,evidence/'not-created.json')
    except ValueError as error:rejected.append({'case':label,'reason':str(error)})
    else:raise AssertionError(label+' unexpectedly accepted')
    assert not (evidence/'not-created.json').exists() and digest(db/'status')==image_status
   refused('installed builder is not an image',selected_image=root)
   changed=copy.deepcopy(qa_record)
   changed['payload']['/usr/bin/unreviewed-runtime']=next(row for row in core_record['payload'].values() if 'sha256' in row)
   refused('QA record contains an unrelated runtime file',selected_qa=changed)
   maintainer=db/'info/python-test-support.postrm';maintainer.write_text('#!/bin/sh\nexit 0\n')
   refused('QA maintainer script is not authorized');maintainer.unlink()
   listing=db/'info/python-test-support.list';prior_list=listing.read_bytes()
   listing.write_bytes(prior_list+b'/usr/bin/unreviewed-runtime\n')
   refused('unexpected QA database ownership');listing.write_bytes(prior_list)
   changed_relative=next(path for path in plan['transferred_paths'] if path.endswith('.py'))
   changed_path=target/changed_relative.lstrip('/');original_bytes=changed_path.read_bytes();original_time=changed_path.stat().st_mtime_ns
   changed_path.write_bytes(original_bytes+b'\n# changed private QA fixture\n')
   refused('changed installed image QA bytes');changed_path.write_bytes(original_bytes);os.utime(changed_path,ns=(original_time,original_time))
   # A separate real image demonstrates that successful Dpkg exit alone is
   # insufficient: untracked QA remnants must fail the postcondition.
   residual=base/'residual-qa-image';shutil.copytree(target,residual,symlinks=True)
   extra=residual/'usr/lib/python3.14/test/toddy-untracked.txt';extra.write_text('private residual fixture\n')
   try:remover(backend,residual,core_record,qa_record,evidence/'residual.json')
   except ValueError as error:
    assert 'residual data' in str(error),str(error)
    rejected.append({'case':'untracked QA after actual native purge','reason':str(error)})
   else:raise AssertionError('Untracked image QA data accepted')
   partial=json.loads((evidence/'residual.json').read_text())
   assert partial['native_exit']==0 and not partial['complete'] and extra.is_file(),partial
   removed=remover(backend,target,core_record,qa_record,evidence/'removed.json')
   assert removed['complete'] and removed['native_exit']==0,removed
   final_keys=audit_keys(target)
   assert final_keys['findings']==other_key_findings,final_keys
   runtime=subprocess.run(['chroot',str(target),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
    '/usr/bin/python3','-I','-B','-c','import ssl, sqlite3, ctypes, unittest; db=sqlite3.connect(":memory:"); assert db.execute("select 6*7").fetchone()==(42,); unittest.TestCase().assertTrue(ssl.OPENSSL_VERSION); print("NATIVE_RUNTIME_WITHOUT_QA_OK", ssl.OPENSSL_VERSION)'],capture_output=True,text=True,check=True)
   try:remover(backend,target,core_record,qa_record,evidence/'removed.json')
   except ValueError as error:
    assert 'Preserve prior' in str(error),str(error)
    rejected.append({'case':'existing removal attempt is preserved','reason':str(error)})
   else:raise AssertionError('Existing removal journal overwritten')
   image_removal_result={'complete':True,'native_removal':removed,'residual_qa_rejection':partial,
    'native_logs':{p.name:p.read_text() for p in evidence.glob('*.dpkg.log')},
    'key_marker_audit_before':initial_keys,'key_marker_audit_after':final_keys,
    'qa_key_marker_findings_removed':len(qa_key_findings),
    'remaining_marker_findings_require_separate_review':len(other_key_findings),
    'release_credential_audit_accepted':False,
    'runtime_exit':runtime.returncode,'runtime_stdout':runtime.stdout,'release_image_or_boot_accepted':False}
 assert digest(root/'var/lib/dpkg/status')==before
 print(json.dumps({'plan':plan,'bundle':bundle,'bundle_native_archive_controls':controls,
  'bundle_archive_sha256':{'core':core_record['archive_sha256'],'qa':qa_record['archive_sha256']},
  'native_archive_reextraction_matches_complete_payloads':True,'compression_threads':2,
  'negative_cases':rejected,'restored_staging_accepted':True,
  'private_configured_transaction':transaction_result,
  'private_image_qa_removal':image_removal_result,
  'actual_installed_bytes_modes_owners_timestamps_checked':True,
  'installed_status_unchanged':True,'native_package_cache_changed':False,'production_cli_dispatched':False,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(body)).hexdigest() for name,body in SOURCES.items()},
  'fixture_removed_after_checks':True},indent=2))
except BaseException:
 print('Preserved Python QA handoff fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources)).replace('TRANSACTION', repr(options.transaction)).replace('IMAGE_REMOVAL', repr(options.image_removal))
r = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
                   input=script, text=True, capture_output=True)
p = Path('.local/logs/h11-python-qa-' + ('image-removal' if options.image_removal else 'transaction' if options.transaction else 'handoff-plan') + '-probe.json')
data = (json.dumps({'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
p.with_name(p.stem + '.' + sha + '.json').write_bytes(data)
p.write_bytes(data)
print(r.stdout, r.stderr)
print('exit', r.returncode, 'SHA256', sha)
r.check_returncode()
