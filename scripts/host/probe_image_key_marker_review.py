#!/usr/bin/env python3
"""Exercise marker review in an actual private native OpenSSL package closure."""
import base64
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {name: base64.b64encode((ROOT / 'scripts/build/h11' / name).read_bytes()).decode()
           for name in ('review_image_key_markers.py', 'audit_private_key_material.py', 'require_gate.py')}
REMOTE = r'''
import base64,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-key-marker-review-',dir=root/'tmp'))
print('KEY_MARKER_FIXTURE '+str(base),flush=True)
for name,body in SOURCES.items():(base/name).write_bytes(base64.b64decode(body))
sys.path.insert(0,str(base))
from review_image_key_markers import review, PREFIX, REVIEWED
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before=digest(root/'var/lib/dpkg/status')
try:
 raw=backend.run('dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\t${Pre-Depends}\n',capture_output=True,text=True).stdout
 installed={}
 for line in raw.splitlines():
  name,version,arch,state,depends,predepends=line.split('\t')
  if state=='install ok installed':installed[name]=(version,arch,depends+','+predepends)
 pending=['openssl','filesystem-layout'];selected=set()
 # The original eleven-package marker fixture deliberately did not prove runtime
 # closure. H07's prepared metadata closure adds these measured providers.
 if RUNTIME_AUDIT:pending.extend(['coreutils','libxcrypt'])
 while pending:
  name=pending.pop()
  if name in selected:continue
  selected.add(name)
  for group in installed[name][2].split(','):
   if not group.strip():continue
   alternatives=[re.match(r'\s*([a-z0-9][a-z0-9+.-]*)',part).group(1) for part in group.split('|')]
   chosen=next((candidate for candidate in alternatives if candidate in installed),None)
   assert chosen is not None,group
   pending.append(chosen)
 cache=base/'archives';cache.mkdir();archives=[]
 for name in sorted(selected):
  version,arch,_=installed[name];stem=f'{name}_{version}_{arch}'
  record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
  source=Path('/var/cache/toddy/packages')/(stem+'.deb')
  assert record['installed'] and digest(source)==record['archive_sha256']
  copied=cache/source.name;shutil.copy2(source,copied);assert digest(copied)==record['archive_sha256']
  archives.append(copied)
 image=base/'image';db=image/'var/lib/dpkg';db.mkdir(parents=True);(db/'status').touch()
 with (base/'native-install.log').open('w') as log:
  backend.run('dpkg','--root=/'+str(image.relative_to(root)),'--unpack',
   *('/'+str(path.relative_to(root)) for path in archives),stdout=log,stderr=subprocess.STDOUT)
  backend.run('dpkg','--root=/'+str(image.relative_to(root)),'--configure','--pending',stdout=log,stderr=subprocess.STDOUT)
 def check():return review(backend,image)
 payload_result=None
 if PAYLOAD_AUDIT:
  from image_payload import audit as audit_payload
  def payload_check():return audit_payload(backend,image)
  payload_positive=payload_check()
  assert payload_positive['owned_payload_check_passed'] and payload_positive['configured_packages']==len(selected)
  assert not payload_positive['unowned_generated_state_audited'] and not payload_positive['dependency_closure_verified']
  payload_cases=[]
  def payload_failure(label):
   result=payload_check();assert not result['owned_payload_check_passed'] and result['findings'],label
   payload_cases.append({'case':label,'findings':result['findings']})
  executable=image/'usr/bin/openssl';original=executable.read_bytes();metadata=executable.stat()
  executable.write_bytes(original+b'\nprivate corruption probe\n');payload_failure('changed executable bytes')
  executable.write_bytes(original);os.utime(executable,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
  conffile=image/(db/'info/openssl.conffiles').read_text().splitlines()[0].lstrip('/')
  config_bytes=conffile.read_bytes();config_stat=conffile.stat()
  conffile.write_bytes(config_bytes+b'\n# unqualified private configuration change\n');payload_failure('changed ordinary conffile')
  conffile.write_bytes(config_bytes);os.utime(conffile,ns=(config_stat.st_atime_ns,config_stat.st_mtime_ns))
  held=executable.with_suffix('.private-held');executable.rename(held);payload_failure('missing recorded executable');held.rename(executable)
  alias=image/'lib';original_link=alias.readlink();alias.unlink();alias.symlink_to('usr/share')
  payload_failure('changed owned link');alias.unlink();alias.symlink_to(original_link)
  os.chown(executable,1,0);payload_failure('changed numeric file owner');os.chown(executable,metadata.st_uid,metadata.st_gid)
  directory=image/'usr/share/doc/openssl';mode=directory.stat().st_mode & 0o7777
  directory.chmod(0o700);payload_failure('changed owned directory mode');directory.chmod(mode)
  sums=db/'info/openssl.md5sums';sum_bytes=sums.read_bytes()
  sums.write_bytes(b'0'*32+sum_bytes[32:]);payload_failure('changed native MD5 value');sums.write_bytes(sum_bytes)
  def payload_refused(label,call):
   try:call()
   except ValueError as error:payload_cases.append({'case':label,'reason':str(error)})
   else:raise AssertionError(label+' was accepted')
  listing=db/'info/openssl.list';list_bytes=listing.read_bytes()
  listing.write_bytes(list_bytes+b'/usr/bin/unowned-private-probe\n')
  payload_refused('extra native ownership path',payload_check);listing.write_bytes(list_bytes)
  bad=base/'payload-bad-records';bad.mkdir()
  for name in selected:
   version,arch,_=installed[name];filename=f'{name}_{version}_{arch}.json'
   data=json.loads((Path('/var/log/toddy/packages')/filename).read_text())
   if name=='openssl':data['archive_sha256']='0'*64
   (bad/filename).write_text(json.dumps(data))
  payload_refused('changed own archive identity',lambda:audit_payload(backend,image,records_directory=bad))
  payload_refused('live transformation without owned base configuration',lambda:audit_payload(backend,image,live_profile=True))
  restored=payload_check();assert restored['owned_payload_check_passed'] and not restored['qualified_live_transformations']
  payload_result={'positive':payload_positive,'negative_cases':payload_cases,'restored_owned_payload_passed':True,
   'component_sha256':digest(base/'image_payload.py'),'live_profile_positive_verified':False,
   'full_image_accepted':False}
 runtime_result=None
 if RUNTIME_AUDIT:
  import image_runtime
  runtime_entries={}
  for name in selected:
   version,arch,_=installed[name]
   record=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
   runtime_entries.update(record['payload'])
  runtime_positive=image_runtime.audit(backend,image,runtime_entries)
  assert runtime_positive['runtime_availability_check_passed'],runtime_positive['findings']
  assert runtime_positive['counts']['dynamic-executable']>10 and runtime_positive['counts']['script']>10
  runtime_cases=[]
  def runtime_refused(label,call):
   try:call()
   except (ValueError,OSError) as error:runtime_cases.append({'case':label,'reason':str(error)})
   else:raise AssertionError(label+' was accepted')
  def inspect_openssl():return image_runtime.executable(backend,image,'/usr/bin/openssl',runtime_entries)
  library=image/'usr/lib/libcrypto.so.4';saved=base/'held-libcrypto'
  assert library.is_file() and not library.is_symlink()
  library.rename(saved);runtime_refused('actual loader rejects missing native library',inspect_openssl);saved.rename(library)
  actual_loader=image/'usr/lib/ld-linux-x86-64.so.2';saved_loader=base/'held-loader'
  actual_loader.rename(saved_loader);runtime_refused('missing image interpreter',inspect_openssl);saved_loader.rename(actual_loader)
  without=dict(runtime_entries);del without['/usr/lib/libcrypto.so.4']
  runtime_refused('resolved library lacks native ownership',lambda:image_runtime.executable(backend,image,'/usr/bin/openssl',without))
  runtime_refused('builder root is not an image',lambda:image_runtime.audit(backend,root,runtime_entries))
  shell=image/'usr/bin/bash';oldmode=shell.stat().st_mode & 0o7777
  shell.chmod(0o644)
  runtime_refused('shebang interpreter loses execute permission',lambda:image_runtime.shebang(image,'/private-probe',b'#!/bin/bash\n',runtime_entries))
  shell.chmod(oldmode)
  runtime_refused('missing absolute shebang provider',lambda:image_runtime.shebang(image,'/private-probe',b'#!/usr/bin/absent-toddy-probe\n',runtime_entries))
  runtime_refused('relative shebang provider',lambda:image_runtime.shebang(image,'/private-probe',b'#!bash\n',runtime_entries))
  runtime_refused('builder-only interpreter',lambda:image_runtime.shebang(image,'/private-probe',b'#!/tools/bin/bash\n',runtime_entries))
  restored_runtime=image_runtime.audit(backend,image,runtime_entries)
  assert restored_runtime['runtime_availability_check_passed'],restored_runtime['findings']
  runtime_result={'positive':runtime_positive,'negative_cases':runtime_cases,
   'restored_runtime_passed':True,'component_sha256':digest(base/'image_runtime.py'),
   'complete_dependency_closure_verified':False}
 passed=check()
 assert passed['private_key_marker_check_passed'] and len(passed['raw_scan']['findings'])==6
 assert len(passed['qualified_document_examples'])==6 and not passed['unresolved_findings']
 assert not passed['whole_image_credential_audit_accepted'] and not passed['raw_findings_suppressed']
 cases=[]
 def report_failure(label,result,count):
  assert not result['private_key_marker_check_passed'] and len(result['unresolved_findings'])==count
  cases.append({'case':label,'unresolved_findings':result['unresolved_findings'],
    'qualified_examples':len(result['qualified_document_examples']),'marker_check_passed':False})
 manual=image/(PREFIX+'man3/PEM_read.pod')[1:];original=manual.read_bytes();metadata=manual.stat()
 manual.write_bytes(original+b'\nChanged private probe document.\n')
 report_failure('changed reviewed document',check(),1)
 manual.write_bytes(original);os.utime(manual,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
 duplicate=manual.with_name('unreviewed-copy.pod');shutil.copy2(manual,duplicate)
 report_failure('identical example at an unreviewed path',check(),1);duplicate.unlink()
 # Generate an actual disposable key, verify it parses, then prove rejection.
 # Keep contents private and out of both console and the evidence report.
 key=image/'root/private-probe-key.pem';key.parent.mkdir(mode=0o700,exist_ok=True)
 with key.open('xb') as stream:
  os.fchmod(stream.fileno(),0o600)
  backend.run('openssl','genpkey','-algorithm','ED25519',stdout=stream,stderr=subprocess.PIPE)
 backend.run('openssl','pkey','-in','/'+str(key.relative_to(root)),'-noout','-check',capture_output=True)
 report_failure('real generated private key',check(),1);key.unlink()
 fifo=image/'root/private-probe-fifo';os.mkfifo(fifo,0o600)
 special=check();assert not special['private_key_marker_check_passed'] and special['raw_scan']['special_nodes_not_read']==1
 cases.append({'case':'unread special node','marker_check_passed':False});fifo.unlink()
 def refused(label,call):
  try:call()
  except ValueError as error:cases.append({'case':label,'reason':str(error)})
  else:raise AssertionError(label+' was accepted')
 manual.chmod(0o600);refused('changed manual metadata',check);manual.chmod(metadata.st_mode & 0o7777)
 status=(db/'status').read_bytes()
 changed,count=re.subn(rb'(Package: openssl\nStatus: )install ok installed',rb'\1deinstall ok config-files',status)
 assert count==1
 (db/'status').write_bytes(changed);refused('unconfigured OpenSSL image identity',check);(db/'status').write_bytes(status)
 bad_records=base/'bad-records';bad_records.mkdir()
 version,arch,_=installed['openssl'];record_name=f'openssl_{version}_{arch}.json'
 bad_record=json.loads((Path('/var/log/toddy/packages')/record_name).read_text());bad_record['archive_sha256']='0'*64
 (bad_records/record_name).write_text(json.dumps(bad_record))
 refused('changed own archive provenance',lambda:review(backend,image,records=bad_records))
 refused('installed builder is not a staged image',lambda:review(backend,root))
 gate=subprocess.run([sys.executable,'-B',str(base/'review_image_key_markers.py'),str(image)],
  env=dict(os.environ,PYTHONPATH='/opt/toddy-build/scripts/build'),capture_output=True,text=True)
 assert gate.returncode!=0 and 'H11 requires H10 completed and H11 in_progress' in gate.stderr
 cases.append({'case':'premature production CLI','exit':gate.returncode,'required_gate':'H10 completed and H11 in_progress'})
 final=check();assert final['raw_scan']['findings']==passed['raw_scan']['findings'] and final['private_key_marker_check_passed']
 attribution_result=None
 if ATTRIBUTION_AUDIT:
  import copy,stat
  import image_attribution as attribution
  import copy_selected_root,live_accounts,package_database
  copied=copy_selected_root.snapshot(image,copy_selected_root.tree_names(image))
  own={}
  for name in selected:
   version,arch,_=installed[name]
   own[name]=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
  plan=attribution.owned_plan(own,copied)
  attribution.declare_database(plan,package_database.snapshot(db))
  baseline=json.loads(base64.b64decode(ACCOUNT_BASELINE))
  accounts=live_accounts.stage_accounts(image,baseline)
  attribution.declare_accounts(plan,baseline)
  def attributed():return attribution.audit(backend,image,plan,copied['hardlink_groups'])
  positive=attributed();assert positive['attribution_check_passed'],positive
  attribution_cases=[]
  def attribution_failure(label):
   result=attributed();assert not result['attribution_check_passed'],label
   attribution_cases.append({'case':label,'result':result})
  extra=image/'root/private-build-data';extra.write_text('Synthetic data must not enter the image.\n')
  attribution_failure('undeclared build data');extra.unlink()
  outside=base/'outside-sentinel';outside.write_text('Do not import this private fixture.\n')
  link=image/'root/outside-alias';link.symlink_to(outside)
  attribution_failure('undeclared outside symlink');link.unlink()
  shadow=image/'etc/shadow';shadow_bytes=shadow.read_bytes()
  shadow.write_bytes(shadow_bytes.replace(b'root:!',b'root:',1));attribution_failure('changed locked account state');shadow.write_bytes(shadow_bytes)
  shadow.chmod(0o644);attribution_failure('changed account permissions');shadow.chmod(0o600)
  os.setxattr(shadow,'user.toddy-probe',b'not-a-secret');attribution_failure('undeclared account extended attribute');os.removexattr(shadow,'user.toddy-probe')
  identity=image/'etc/machine-id';identity.write_text('1'*32+'\n');attribution_failure('inherited machine identity');identity.write_bytes(b'')
  status_bytes=(db/'status').read_bytes();(db/'status').write_bytes(status_bytes+b'\n');attribution_failure('changed generated native database');(db/'status').write_bytes(status_bytes)
  pairs=[group for group in copied['hardlink_groups'] if stat.S_ISREG((image/group[0]).lstat().st_mode)]
  assert pairs,'Real native package fixture lacks a hardlink group; revise fixture, not the assertion'
  name,peer=pairs[0][:2];path=image/name;other=image/peer;held=base/'split-hardlink'
  shutil.copy2(path,held);path.unlink();shutil.copy2(held,path)
  attribution_failure('split native hardlink group');path.unlink();os.link(other,path);held.unlink()
  fifo=image/'root/unreviewed-fifo';os.mkfifo(fifo,0o600)
  try:attributed()
  except ValueError as error:attribution_cases.append({'case':'special image node','reason':str(error)})
  else:raise AssertionError('Special image node accepted')
  fifo.unlink()
  try:attribution.add(copy.deepcopy(plan),'../outside',attribution.directory(),'invalid-fixture')
  except ValueError as error:attribution_cases.append({'case':'traversal declaration','reason':str(error)})
  else:raise AssertionError('Traversal declaration accepted')
  restored_attribution=attributed();assert restored_attribution['attribution_check_passed'],restored_attribution
  attribution_result={'positive':positive,'negative_cases':attribution_cases,'fresh_accounts':accounts,
    'restored_attribution_passed':True,'source_hardlink_groups':len(copied['hardlink_groups']),
    'component_sha256':digest(base/'image_attribution.py'),
    'scope':'Actual eleven-package private root, native database and generated account state only',
    'complete_foundation_profile_verified':False,'release_image_or_boot_accepted':False}
 assert digest(root/'var/lib/dpkg/status')==before
 result={'fixture':str(base),'configured_packages':sorted(selected),'positive':passed,'negative_cases':cases,
  'payload_audit':payload_result,'runtime_audit':runtime_result,
  'attribution_audit':attribution_result,
  'native_install_log':(base/'native-install.log').read_text(),
  'native_install_log_sha256':digest(base/'native-install.log'),'builder_status_sha256':before,
  'installed_target_modified':False,'component_sha256':digest(base/'review_image_key_markers.py'),
  'real_private_key_rejected':True,'whole_image_credential_audit_accepted':False,'release_image_or_boot_accepted':False}
 (base/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('KEY_MARKER_RESULT '+json.dumps(result),flush=True)
 shutil.rmtree(base)
except BaseException:
 print('PRESERVED_KEY_MARKER_FIXTURE '+str(base),flush=True)
 raise
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', action='store_true', help='Also verify owned image payload and native metadata against real corruption cases')
    parser.add_argument('--attribution', action='store_true', help='Also verify declared image entries, account data and extended metadata')
    parser.add_argument('--runtime', action='store_true', help='Also verify actual image loader and shebang providers')
    options = parser.parse_args()
    if options.attribution or options.runtime:
        options.payload = True
    sources = dict(SOURCES)
    if options.payload:
        for name in ('image_payload.py', 'fresh_directories.py', 'live_accounts.py',
                     'live_configuration.py', 'root_inventory.py', 'package_database.py'):
            sources[name] = base64.b64encode((ROOT / 'scripts/build/h10' / name).read_bytes()).decode()
    if options.attribution:
        for name in ('image_attribution.py', 'copy_selected_root.py', 'live_console.py'):
            sources[name] = base64.b64encode((ROOT / 'scripts/build/h10' / name).read_bytes()).decode()
    if options.runtime:
        sources['image_runtime.py'] = base64.b64encode((ROOT / 'scripts/build/h10/image_runtime.py').read_bytes()).decode()
        sources['audit_native_elf.py'] = base64.b64encode((ROOT / 'scripts/build/audit_native_elf.py').read_bytes()).decode()
    baseline = base64.b64encode((ROOT / 'config/live-account-baseline.json').read_bytes()).decode()
    result = subprocess.run(ssh_args() + ['python3 -B -'],
        input='SOURCES=' + repr(sources) + '\nPAYLOAD_AUDIT=' + repr(options.payload)
            + '\nATTRIBUTION_AUDIT=' + repr(options.attribution) + '\nRUNTIME_AUDIT=' + repr(options.runtime)
            + '\nACCOUNT_BASELINE=' + repr(baseline) + '\n' + REMOTE,
        text=True, capture_output=True, timeout=600)
    raw = (result.stdout + result.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h11-image-key-marker-review-' + sha + '.log')
    path.write_bytes(raw)
    print(json.dumps({'exit': result.returncode, 'report': str(path), 'sha256': sha}))
    if result.returncode:
        print(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    report = json.loads(next(line.removeprefix('KEY_MARKER_RESULT ') for line in result.stdout.splitlines()
                             if line.startswith('KEY_MARKER_RESULT ')))
    print(json.dumps({'configured_packages': len(report['configured_packages']),
        'qualified_examples': len(report['positive']['qualified_document_examples']),
        'negative_cases': len(report['negative_cases']), 'real_private_key_rejected': report['real_private_key_rejected'],
        'payload_negative_cases': len(report['payload_audit']['negative_cases']) if report['payload_audit'] else None,
        'attribution_negative_cases': len(report['attribution_audit']['negative_cases']) if report['attribution_audit'] else None,
        'runtime_negative_cases': len(report['runtime_audit']['negative_cases']) if report['runtime_audit'] else None,
        'whole_image_credential_audit_accepted': False}))


if __name__ == '__main__':
    main()
