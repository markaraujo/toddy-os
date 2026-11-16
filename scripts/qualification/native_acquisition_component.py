#!/usr/bin/python3 -I
"""Root-only disposable installed-VM component qualification, never a product bypass.

Actual APT/Journal are exercised directly from trusted signed component inputs.
Production NativeCatalog readiness is neither replaced nor overridden. The output
is native-components only; full helper/UI acceptance needs another clean overlay.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from runtime.setup.pending import SetupError,_strict,_encode
from runtime.setup.releases import (DIRECTORY,SOURCES,signature,private_metadata,sha,exact,
    validate_declaration,describe,code_pinset,COMPONENT_CHECKS,LOCAL_CHECKS)
from runtime.shared.openpgp import public_key_only
from runtime.setup.platform import installed_toddy
from runtime.setup.native_backend import NativeBackend,command
from runtime.setup.acquisition_journal import Journal
from runtime.setup.native_acquire import active

CONTEXT=Path('/var/lib/toddy/native-acquisition-qualification-1')
MARKER=Path('/etc/toddy/native-acquisition-qualification.json')
HELPER='/usr/lib/toddy/setup/native_acquire.py'


def save(path,value):
    assert path.parent==CONTEXT and not path.is_symlink()
    part=path.with_suffix('.part')
    with part.open('xb') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(_encode(value)+b'\n');stream.flush();os.fsync(stream.fileno())
    os.replace(part,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def read(path):
    return _strict(private_metadata(path))


def target():
    assert os.getuid()==os.geteuid()==0
    installed_toddy()
    kind=subprocess.check_output(['/usr/bin/systemd-detect-virt','--vm'],text=True).strip()
    if kind not in ('qemu','kvm'):raise SetupError('qualification_disposable_vm_required')
    marker=read(MARKER)
    exact(marker,('version','scope','disposable','owner_uid','root_uuid'))
    if marker['version']!=1 or marker['scope']!='native-acquisition-components' or marker['disposable'] is not True or type(marker['owner_uid']) is not int or not 1000<=marker['owner_uid']<2**31:
        raise SetupError('qualification_disposable_vm_required')
    actual=subprocess.check_output(['/usr/bin/findmnt','-rn','-o','UUID','--mountpoint','/'],text=True).strip()
    if not actual or actual!=marker['root_uuid']:raise SetupError('qualification_root_changed')
    active(marker['owner_uid'])
    private_metadata(CONTEXT/'candidates.json') # Parent stages only reviewed fixed inputs.
    return marker


class Components:
    def __init__(self,*,describe_review=True):
        self.describe_review=describe_review
        self.directory=DIRECTORY
        trust=read(DIRECTORY/'trust.json');exact(trust,('version','fingerprint','keyring_sha256'))
        key=private_metadata(DIRECTORY/'archive-keyring.gpg',maximum=1048576);public_key_only(key)
        if sha(key)!=trust['keyring_sha256']:raise SetupError('release_trust')
        self.fingerprint=trust['fingerprint'];self.verify=signature
        data=private_metadata(CONTEXT/'candidates.json')
        if signature(DIRECTORY/'archive-keyring.gpg',CONTEXT/'candidates.json.asc',CONTEXT/'candidates.json')!=self.fingerprint:
            raise SetupError('release_signature')
        candidate=_strict(data);exact(candidate,('version','generation','repository','release'))
        if type(candidate['version']) is not int or candidate['version']!=1 or type(candidate['generation']) is not int or not 1<=candidate['generation']<2**53:
            raise SetupError('qualification_candidate_schema')
        repo=candidate['repository'];exact(repo,('id','sources_sha256','inrelease_sha256','inrelease_bytes'))
        if repo['id']!='toddy-native' or sha(private_metadata(SOURCES))!=repo['sources_sha256']:
            raise SetupError('release_origin')
        source=private_metadata(SOURCES).decode('ascii',errors='strict').strip()
        match=re.fullmatch(r'deb \[signed-by='+re.escape(str(DIRECTORY/'archive-keyring.gpg'))+r'\] (\S+) (?:[a-z0-9][a-z0-9.-]{0,63}|\./)(?: main)?',source)
        if not match:raise SetupError('release_origin')
        from urllib.parse import urlsplit
        origin=urlsplit(match[1])
        if origin.username or origin.password or origin.query or origin.fragment or not (
            origin.scheme=='https' and origin.hostname or origin.scheme=='file' and not origin.netloc and origin.path==str(DIRECTORY/'repository')):
            raise SetupError('release_origin')
        validate_declaration(candidate['release'],directory=DIRECTORY)
        self.value={'repository':repo};self.release=candidate['release'];self.revision=sha(data)
        self.code=code_pinset()
        # Direct component imports must be byte-identical to the installed
        # helper/UI build whose hash pins will be published, never a newer tree.
        for virtual,digest in self.code['files'].items():
            if virtual.startswith('/usr/lib/toddy/'):
                source=ROOT/'runtime'/virtual.removeprefix('/usr/lib/toddy/')
            elif virtual.endswith('Toddy.AcquireNative.policy'):
                source=ROOT/'runtime/setup/io.github.markaraujo.Toddy.AcquireNative.policy'
            else:continue
            if not source.is_file() and source.name!='__init__.py':raise SetupError('qualification_source_installed_mismatch')
            if source.is_file() and sha(source.read_bytes())!=digest:raise SetupError('qualification_source_installed_mismatch')
        self.trust={'fingerprint':self.fingerprint,'keyring_sha256':trust['keyring_sha256'],
            'sources_sha256':repo['sources_sha256'],'inrelease_sha256':repo['inrelease_sha256']}
        self.review=describe(self.release,revision=self.revision,generation=candidate['generation'],origin=match[1],level='unqualified-native-component-input') if describe_review else None

    def ensure_current(self):
        current=Components(describe_review=self.describe_review)
        if (current.revision,current.code,current.trust)!=(self.revision,self.code,self.trust):
            raise SetupError('qualification_inputs_changed')


def dpkg_digest():
    return sha(private_metadata(Path('/var/lib/dpkg/status'),maximum=64*1024**2))


def activation(uid,*,after=False):
    commands=[['/usr/bin/systemctl','show','toddy-executor.service','-p','ActiveState','--value'],
        ['/usr/bin/systemctl','--user','--machine',pwd.getpwuid(uid).pw_name+'@.host',
            'show','toddy-agent.service','-p','ActiveState','--value']]
    states=[]
    for argv in commands:
        code,data=command(argv)
        state=data.decode('ascii',errors='strict').strip()
        if state in ('active','activating','reloading') or after and (code or state not in ('inactive','failed')):
            raise SetupError('qualification_service_activation')
        states.append(state if not code else 'not-loaded-before-install')
    code,_=command(['/usr/bin/pgrep','-x','llama-server'])
    if code!=1:raise SetupError('qualification_runtime_activation')
    if Path('/var/lib/toddy/executor/state.sqlite').exists():
        raise SetupError('qualification_grant_state_present')
    return states


def user_state(uid):
    # Only fixture app-tree metadata, never keyring values, model bytes or text.
    home=Path(pwd.getpwuid(uid).pw_dir)
    rows=[]
    for relative in ('.local/state/toddy','.local/share/toddy','.config/toddy'):
        base=home/relative
        if not base.exists():continue
        for path in [base,*base.rglob('*')]:
            info=path.lstat();rows.append((str(path.relative_to(home)),info.st_ino,info.st_size,info.st_mtime_ns,info.st_mode))
    return sha(_encode(sorted(rows)))


def case_path(case,suffix='request'):
    if case not in ('stop','offline','write'):raise SetupError('qualification_case')
    return CONTEXT/(case+'-'+suffix+'.json')


def request(case,adapter,marker):
    path=case_path(case)
    if path.exists():raise SetupError('qualification_existing_case')
    if shutil.disk_usage('/').free<16*1024**3+2*adapter.review['download_bytes']+2*adapter.review['installed_bytes']+512*1024**2:
        raise SetupError('qualification_development_reserve')
    backend=NativeBackend(adapter)
    before=backend.query([row['name'] for row in adapter.release['packages']])
    primary={'toddy-agent','toddy-executor'} if adapter.release['id']!='local-runtime' else {'llama-cpp'}
    if any(before.get(name) is not None for name in primary):raise SetupError('qualification_primary_not_absent')
    identity=uuid.uuid4().hex
    with closing(Journal()) as journal:
        _,created=journal.accept(marker['owner_uid'],identity,adapter.review)
        if not created:raise SetupError('qualification_duplicate_case')
    row={'version':1,'case':case,'operation_id':identity,'owner_uid':marker['owner_uid'],
        'review':adapter.review,'code_pins':adapter.code,'trust_pins':adapter.trust,
        'package_set_sha256':sha(_encode(adapter.release['packages'])),'root_uuid':marker['root_uuid'],
        'dpkg_before':dpkg_digest(),'user_state_before':user_state(marker['owner_uid']),'inventory_before':before,'activation_before':activation(marker['owner_uid']),
        'driver_sha256':sha(Path(__file__).read_bytes()),'mount_namespace':os.readlink('/proc/self/ns/mnt'),'network_namespace':os.readlink('/proc/self/ns/net')}
    save(path,row)
    print(json.dumps({'state':'awaiting_explicit_owner_action','case':case,'review':adapter.review,
        'command':['/usr/bin/pkexec',HELPER,'cancel' if case=='stop' else 'install',identity,
                   *([] if case=='stop' else [adapter.release['id'],adapter.review['review_sha256'],adapter.review['terms_sha256']])]},sort_keys=True))


def owner_receipt(name,request,action,*,other=False):
    # Captured by the native coordinator from an ACTUAL installed-owner session.
    # It is evidence input, never authorization for the production helper.
    proof=read(CONTEXT/(name+'.json'))
    exact(proof,('version','exec_path','program_sha256','action','requested_uid','exit','stdout'))
    if type(proof['version']) is not int or proof['version']!=1 or type(proof['exit']) is not int or type(proof['requested_uid']) is not int or proof['requested_uid']<1000 or proof['exec_path']!=HELPER or proof['program_sha256']!=request['code_pins']['files'][HELPER] or proof['action']!=action:
        raise SetupError('qualification_owner_receipt')
    output=proof['stdout']
    if other:
        if proof['requested_uid']==request['owner_uid'] or proof['exit'] not in (2,126,127) or output is not None and output.get('ok') is not False:
            raise SetupError('qualification_other_uid_not_denied')
        return proof
    if proof['requested_uid']!=request['owner_uid'] or proof['exit']!=0 or not isinstance(output,dict) or output.get('ok') is not True or output.get('authenticated_uid')!=request['owner_uid'] or \
            output.get('operation_id')!=request['operation_id'] or output.get('review_sha256')!=request['review']['review_sha256']:
        raise SetupError('qualification_owner_receipt')
    return proof


def execute(case,adapter,marker,*,offline_child=False):
    record=read(case_path(case))
    if record['driver_sha256']!=sha(Path(__file__).read_bytes()):raise SetupError('qualification_producer_changed')
    if (record['code_pins'],record['trust_pins'],record['root_uuid'])!=(adapter.code,adapter.trust,marker['root_uuid']):raise SetupError('qualification_inputs_changed')
    if case_path(case,'result').exists():raise SetupError('qualification_case_already_executed')
    if case=='stop':owner_receipt('owner-cancel',record,'cancel')
    if case=='write':owner_receipt('owner-install',record,'install')
    if case=='offline' and not offline_child:
        child=subprocess.run(['/usr/bin/unshare','--mount','--net','--fork','/usr/bin/python3','-I',str(Path(__file__).resolve()),'_offline'])
        if child.returncode:raise SetupError('qualification_offline_child_failed')
        return
    if offline_child:
        if os.readlink('/proc/self/ns/mnt')==record['mount_namespace'] or os.readlink('/proc/self/ns/net')==record['network_namespace']:
            raise SetupError('qualification_private_namespace_required')
        subprocess.run(['/usr/bin/mount','--make-rprivate','/'],check=True)
        if adapter.review['repository_origin'].startswith('file:'):
            subprocess.run(['/usr/bin/mount','-t','tmpfs','-o','size=4096,ro,nosuid,nodev','toddy-qualification-offline',str(DIRECTORY/'repository')],check=True)
    def run(argv,**options):
        code,data=command(argv,**options)
        if case=='write' and argv[0]=='/usr/bin/apt-get' and '--no-download' in argv and code==0:
            # Actual native write finished. Deliberately lose the controller
            # BEFORE canonical postconditions/terminal receipt, never kill dpkg.
            save(CONTEXT/'native-write-returned.json',{'version':1,'operation_id':record['operation_id'],
                'native_writer_exit':0,'code_pins':adapter.code,'trust_pins':adapter.trust,'dpkg_after':dpkg_digest()})
            os._exit(73)
        return code,data
    with closing(Journal(create=False)) as journal:
        row=journal.get(record['owner_uid'],record['operation_id'])
        if row is None or row['state']!='prepared':raise SetupError('qualification_case_not_fresh')
        backend=NativeBackend(adapter,run=run,before_write=lambda:active(record['owner_uid']))
        result=backend.acquire(journal,record['owner_uid'],record['operation_id'],adapter.release,record['review'])
        expected='canceled' if case=='stop' else 'deferred'
        if result['state']!=expected or result['write_intent_recorded'] or dpkg_digest()!=record['dpkg_before'] or backend.query(record['inventory_before'])!=record['inventory_before']:
            raise SetupError('qualification_prewrite_postcondition')
        save(case_path(case,'result'),{'version':1,'case':case,'state':result['state'],'native_exit':0,
            'postconditions_exit':0,'dpkg_unchanged':True,'code_pins':adapter.code,'trust_pins':adapter.trust})


def observe(adapter,marker):
    record=read(case_path('write'))
    if record['driver_sha256']!=sha(Path(__file__).read_bytes()):raise SetupError('qualification_producer_changed')
    if case_path('write','result').exists():raise SetupError('qualification_existing_result')
    returned=read(CONTEXT/'native-write-returned.json')
    if returned['native_writer_exit']!=0 or returned['operation_id']!=record['operation_id']:
        raise SetupError('qualification_no_actual_native_write')
    owner_receipt('owner-reconcile',record,'reconcile');owner_receipt('owner-duplicate',record,'install')
    owner_receipt('other-uid',record,'status',other=True)
    with closing(Journal(create=False,read_only=True)) as journal:
        result=journal.get(record['owner_uid'],record['operation_id'])
        if result is None or result['state']!='installed':raise SetupError('qualification_not_reconciled')
    backend=NativeBackend(adapter)
    if backend.query(record['inventory_before'])!={row['name']:row['version'] for row in adapter.release['packages']}:
        raise SetupError('qualification_package_inventory')
    backend.postconditions(adapter.release);states=activation(record['owner_uid'],after=True)
    if user_state(record['owner_uid'])!=record['user_state_before']:raise SetupError('qualification_user_state_changed')
    # Require the duplicate owner result to observe the same terminal effect.
    duplicate=read(CONTEXT/'owner-duplicate.json')['stdout']
    if duplicate.get('state')!='installed' or returned['dpkg_after']!=dpkg_digest():raise SetupError('qualification_native_replay_or_drift')
    save(case_path('write','result'),{'version':1,'case':'write','native_exit':73,'native_writer_exit':0,
        'postconditions_exit':0,'state':'installed-after-observation','activation':states,
        'code_pins':adapter.code,'trust_pins':adapter.trust,'dpkg_unchanged_after_completed_write':True})



def acquisition_snapshot(backend):
    """Hash actual operation/cache state without exporting bodies or changing it."""
    roots=(Path('/var/lib/toddy/setup-acquisition'),backend.cache)
    result={}
    for root in roots:
        if not os.path.lexists(root):result[str(root)]={'exists':False};continue
        if root.resolve()!=root or not root.is_dir():raise SetupError('qualification_acquisition_state_custody')
        rows=[];device=root.stat().st_dev
        for path in (root,*sorted(root.rglob('*'))):
            info=path.lstat()
            if info.st_dev!=device or path.is_symlink() or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise SetupError('qualification_acquisition_state_custody')
            row=[path.relative_to(root).as_posix(),info.st_mode,info.st_uid,info.st_gid,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns]
            if stat.S_ISREG(info.st_mode):
                with path.open('rb') as stream:row.append(__import__('hashlib').file_digest(stream,'sha256').hexdigest())
            rows.append(row)
        result[str(root)]={'exists':True,'entries':len(rows),'state_sha256':sha(_encode(rows))}
    return result


def operation_snapshot(journal,uid,identity):
    if journal is None:return {'database_exists':False,'test_operation':None,'operations':0,'native_write_intents':0}
    return {'database_exists':True,'test_operation':journal.get(uid,identity),
        'operations':journal.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],
        'native_write_intents':journal.db.execute('SELECT COUNT(*) FROM operations WHERE mutation!=0').fetchone()[0]}


def cpu_denial(adapter,marker):
    """Real unsupported installed CPU through unchanged default NativeBackend."""
    from runtime.setup.runtime_compat import cpu_features,CPU_FLAGS
    output=CONTEXT/'native-cpu-denial.json';intent=CONTEXT/'cpu-denial-intent.json'
    if os.path.lexists(output) or os.path.lexists(intent):raise SetupError('qualification_existing_cpu_case')
    if adapter.release['id'] not in ('local-runtime','agent-local') or not any(row['name']=='llama-cpp' for row in adapter.release['packages']):
        raise SetupError('qualification_local_candidate_required')
    architecture,flags=cpu_features();missing=sorted(set(CPU_FLAGS)-flags)
    if architecture!='x86_64' or not missing:raise SetupError('qualification_actual_unsupported_cpu_required')
    if adapter.review is not None:raise SetupError('qualification_unsupported_review_forbidden')
    adapter.ensure_current();active(marker['owner_uid'])
    backend=NativeBackend(adapter)
    if backend.run is not command or sys.getprofile() is not None:raise SetupError('qualification_unmodified_native_observer_required')
    identity=uuid.uuid4().hex;journal=None
    try:
        if Path('/var/lib/toddy/setup-acquisition/operations.sqlite').exists():journal=Journal(create=False,read_only=True)
        before={'dpkg_sha256':dpkg_digest(),'inventory':backend.query([row['name'] for row in adapter.release['packages']]),
            'acquisition_state':acquisition_snapshot(backend),'operation':operation_snapshot(journal,marker['owner_uid'],identity)}
        if before['operation']['test_operation'] is not None:raise SetupError('qualification_cpu_operation_collision')
        observed={'native_command_calls':0};error_code=None
        save(intent,{'version':1,'kind':'actual-native-cpu-denial-intent','operation_id':identity,'owner_uid':marker['owner_uid'],
            'root_uuid':marker['root_uuid'],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'candidate_sha256':adapter.revision,'code_pins':adapter.code,'trust_pins':adapter.trust,
            'driver_sha256':sha(Path(__file__).read_bytes()),'missing_cpu_flags':missing,'before':before})
        def observe(frame,event,_argument):
            # Observation only: never raises, replaces runner/results or changes
            # hardware. Scope excludes the read-only before/after observations.
            if event=='call' and frame.f_code is command.__code__:observed['native_command_calls']+=1
        sys.setprofile(observe)
        try:
            # No supported review/accepted operation is fabricated. This actual
            # guard must reject before accessing either journal or review.
            backend.acquire(journal,marker['owner_uid'],identity,adapter.release,None)
        except SetupError as error:error_code=str(error)
        finally:sys.setprofile(None)
        after={'dpkg_sha256':dpkg_digest(),'inventory':backend.query([row['name'] for row in adapter.release['packages']]),
            'acquisition_state':acquisition_snapshot(backend),'operation':operation_snapshot(journal,marker['owner_uid'],identity)}
        final_architecture,final_flags=cpu_features()
        if error_code!='native_runtime_cpu_unsupported' or observed['native_command_calls']!=0 or before!=after or (final_architecture,final_flags)!=(architecture,flags):
            raise SetupError('qualification_actual_cpu_denial_not_proven')
        adapter.ensure_current();active(marker['owner_uid'])
        receipt={'version':1,'kind':'actual-installed-native-cpu-denial','native_result':'denied_before_apt',
            'scope':'native-component-eligibility-only','fixture_only':False,'operation_id':identity,
            'root_uuid':marker['root_uuid'],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'candidate_sha256':adapter.revision,'code_pins':adapter.code,'trust_pins':adapter.trust,
            'package_set_sha256':sha(_encode(adapter.release['packages'])),'runtime_profile_sha256':sha(_encode(adapter.release['runtime_profile'])),'driver_sha256':sha(Path(__file__).read_bytes()),
            'architecture':architecture,'required_cpu_flags':CPU_FLAGS,'present_required_cpu_flags':sorted(set(CPU_FLAGS)&flags),
            'missing_cpu_flags':missing,'actual_cpu_flags_sha256':sha(_encode(sorted(flags))),
            'error_code':error_code,'observer_scope':'unchanged NativeBackend.acquire only; baseline/readback queries excluded',**observed,'before':before,'after':after,
            'runtime_activated':False,'model_loaded':False,'final_publication_permitted':False}
        save(output,receipt)
        print(json.dumps({'native_result':receipt['native_result'],'receipt_sha256':sha(output.read_bytes()),
            'native_command_calls':0,'final_publication_permitted':False},sort_keys=True))
        return receipt
    finally:
        if journal is not None:journal.close()



def validate_cpu_receipt(cpu,adapter):
    """Reject bare markers; retain the exact actual denial/state observation."""
    from runtime.setup.runtime_compat import CPU_FLAGS
    if not isinstance(cpu,dict) or cpu.get('kind')!='actual-installed-native-cpu-denial' or cpu.get('native_result')!='denied_before_apt' or cpu.get('scope')!='native-component-eligibility-only' or cpu.get('fixture_only') is not False or cpu.get('error_code')!='native_runtime_cpu_unsupported' or type(cpu.get('native_command_calls')) is not int or cpu['native_command_calls']!=0 or cpu.get('code_pins')!=adapter.code or cpu.get('trust_pins')!=adapter.trust or cpu.get('candidate_sha256')!=adapter.revision or cpu.get('package_set_sha256')!=sha(_encode(adapter.release['packages'])) or cpu.get('runtime_profile_sha256')!=sha(_encode(adapter.release['runtime_profile'])) or cpu.get('driver_sha256')!=sha(Path(__file__).read_bytes()):
        raise SetupError('qualification_actual_masked_cpu_receipt_required')
    missing=cpu.get('missing_cpu_flags');present=cpu.get('present_required_cpu_flags')
    if cpu.get('architecture')!='x86_64' or cpu.get('required_cpu_flags')!=CPU_FLAGS or not isinstance(missing,list) or not missing or not isinstance(present,list) or missing!=sorted(set(missing)) or present!=sorted(set(present)) or set(missing)&set(present) or set(missing)|set(present)!=set(CPU_FLAGS):
        raise SetupError('qualification_actual_masked_cpu_receipt_required')
    before=cpu.get('before');after=cpu.get('after')
    if not isinstance(before,dict) or set(before)!={'dpkg_sha256','inventory','acquisition_state','operation'} or before!=after or not isinstance(before['operation'],dict) or before['operation'].get('test_operation') is not None or any(type(before['operation'].get(key)) is not int or before['operation'][key]<0 for key in ('operations','native_write_intents')):
        raise SetupError('qualification_actual_masked_cpu_receipt_required')
    return True


def report(adapter,marker):
    # No generic pass switch. Every component is derived from retained actual
    # case outputs/owner transport inputs; local masked-CPU proof is additional.
    if (CONTEXT/'component-evidence.json').exists() or (CONTEXT/'component-qualification.json').exists():raise SetupError('qualification_terminal_receipt_immutable')
    for case in ('stop','offline','write'):
        if read(case_path(case))['driver_sha256']!=sha(Path(__file__).read_bytes()):raise SetupError('qualification_producer_changed')
    results={case:read(case_path(case,'result')) for case in ('stop','offline','write')}
    for result in results.values():
        if result['postconditions_exit']!=0 or result['code_pins']!=adapter.code or result['trust_pins']!=adapter.trust:
            raise SetupError('qualification_case_inputs_changed')
    if results['stop']['state']!='canceled' or results['offline']['state']!='deferred' or results['write']['state']!='installed-after-observation':
        raise SetupError('qualification_case_incomplete')
    # Real gpgv tamper check against an independent disposable input copy.
    tampered=CONTEXT/'tampered-candidates.json'
    data=private_metadata(CONTEXT/'candidates.json')
    if tampered.exists():
        if private_metadata(tampered)!=data+b' ':raise SetupError('qualification_changed_tamper_case')
    else:tampered.write_bytes(data+b' ');tampered.chmod(0o600)
    try:signature(DIRECTORY/'archive-keyring.gpg',CONTEXT/'candidates.json.asc',tampered)
    except SetupError as error:
        if str(error)!='release_signature':raise
    else:raise SetupError('qualification_signature_tamper_accepted')
    checks={key:True for key in COMPONENT_CHECKS} # Only after the explicit cases above.
    cpu=None
    if 'llama-cpp' in {row['name'] for row in adapter.release['packages']}:
        cpu=read(CONTEXT/'native-cpu-denial.json')
        validate_cpu_receipt(cpu,adapter)
        checks.update({key:True for key in LOCAL_CHECKS})
    evidence={'version':1,'scope':'installed-native-agent-acquisition','environment':'native-installed-user',
        'fixture_only':False,'qualification_level':'native-components','runner_exit':0,'postconditions_exit':0,
        'package_set_sha256':sha(_encode(adapter.release['packages'])),'code_pins':adapter.code,'trust_pins':adapter.trust,
        'component_results':results,'native_cpu_denial':cpu,'driver_sha256':sha(Path(__file__).read_bytes()),
        'full_helper_ui_flow':'not-tested; must run from another clean overlay with signed preview catalog'}
    save(CONTEXT/'component-evidence.json',evidence)
    value={'version':1,'scope':'installed-native-agent-acquisition','native_result':'passed',
        'qualification_level':'native-components','package_set_sha256':evidence['package_set_sha256'],
        'code_pins':adapter.code,'trust_pins':adapter.trust,'checks':checks,
        'retained_evidence_sha256':sha(_encode(evidence)+b'\n')}
    save(CONTEXT/'component-qualification.json',value)
    print(json.dumps({'qualification_level':'native-components','component_qualification_sha256':sha((CONTEXT/'component-qualification.json').read_bytes()),
        'evidence_sha256':value['retained_evidence_sha256'],'final_publication_permitted':False},sort_keys=True))


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('action',choices=['inspect','prepare-stop','run-stop','prepare-offline','run-offline','prepare-write','run-write-crash','observe-reconcile','cpu-denial','report','_offline'])
    args=parser.parse_args();os.umask(0o077)
    marker=target();adapter=Components(describe_review=args.action!='cpu-denial')
    if args.action=='cpu-denial':cpu_denial(adapter,marker);return
    if args.action=='inspect':
        print(json.dumps({'scope':'unqualified signed component inputs','review':adapter.review,
            'code_pins':adapter.code,'trust_pins':adapter.trust,'ready_for_production_catalog':False},sort_keys=True));return
    if args.action.startswith('prepare-'):request(args.action.removeprefix('prepare-'),adapter,marker)
    elif args.action=='run-stop':execute('stop',adapter,marker)
    elif args.action=='run-offline':execute('offline',adapter,marker)
    elif args.action=='_offline':execute('offline',adapter,marker,offline_child=True)
    elif args.action=='run-write-crash':execute('write',adapter,marker)
    elif args.action=='observe-reconcile':observe(adapter,marker)
    else:report(adapter,marker)


if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt):
        # Preserve all real contexts. Detailed native command evidence is held
        # privately by the coordinator; never turn an exception into a pass.
        print(json.dumps({'scope':'native-components','state':'failed-preserved','final_publication_permitted':False}))
        raise
