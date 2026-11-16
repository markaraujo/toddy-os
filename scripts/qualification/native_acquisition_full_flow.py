#!/usr/bin/python3 -I
"""Read-only assembly of actual production acquisition cases; never executes them.

No component level/boolean can substitute for these independently captured native
production helper/UI and real signed two-version package lifecycle receipts.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts/build/phase2')]
from runtime.setup.pending import SetupError,_strict,_encode
from runtime.setup.platform import installed_toddy
from runtime.setup.native_acquire import active
from runtime.installer.composition import secured
from runtime.setup.releases import NativeCatalog,REQUIRED_CHECKS,LOCAL_CHECKS,code_pinset,private_metadata,signature,sha
import offline_payload as payload

CONTEXT=Path('/var/lib/toddy/native-acquisition-full-flow-1')
MARKER=Path('/etc/toddy/native-acquisition-full-flow.json')
CASES=('install','stop','reconnect','tamper','offline','lifecycle')
HELPER='/usr/lib/toddy/setup/native_acquire.py'


def require(value,code):
    if not value:raise SetupError(code)


def read(path,maximum=4*1024**2):return _strict(private_metadata(Path(path),maximum=maximum))


def guard():
    require(os.getuid()==os.geteuid()==0,'qualification_root_required');installed_toddy()
    kind=subprocess.check_output(['/usr/bin/systemd-detect-virt','--vm'],text=True).strip()
    require(kind in ('qemu','kvm'),'qualification_disposable_vm_required')
    marker=read(MARKER)
    require(set(marker)=={'version','scope','disposable','owner_uid','root_uuid'} and type(marker['version']) is int and marker['version']==1 and marker['scope']=='native-acquisition-full-flow' and marker['disposable'] is True and type(marker['owner_uid']) is int and 1000<=marker['owner_uid']<2**31,'qualification_disposable_vm_required')
    actual=subprocess.check_output(['/usr/bin/findmnt','-rn','-o','UUID','--mountpoint','/'],text=True).strip()
    require(actual and actual==marker['root_uuid'],'qualification_root_changed');active(marker['owner_uid'])
    info=CONTEXT.lstat()
    require(CONTEXT.resolve()==CONTEXT and (info.st_mode,info.st_uid,info.st_gid)==(stat.S_IFDIR|0o700,0,0),'qualification_private_full_context_required')
    return marker


def bindings(catalog,release_id):
    row=catalog.releases[release_id]
    return {'release_id':release_id,'tested_preview_catalog_sha256':catalog.revision,
        'package_set_sha256':sha(_encode(row['packages'])),'code_pins':code_pinset(),
        'trust_pins':{'fingerprint':catalog.fingerprint,'keyring_sha256':catalog.keyring_sha256,
            'sources_sha256':catalog.value['repository']['sources_sha256'],'inrelease_sha256':catalog.value['repository']['inrelease_sha256']}}


def load_case(case,expected,uid):
    path=CONTEXT/(case+'.json');value=read(path)
    require(isinstance(value,dict) and set(value)=={'version','kind','case','environment','fixture_only','bindings','owner_uid','session','boot_id','root_uuid','runner_exit','postconditions_exit','artifacts','observations'},'qualification_full_case_schema')
    require(type(value['version']) is int and value['version']==1 and value['kind']=='actual-production-acquisition-full-flow-case-v1' and value['case']==case and value['environment']=='native-installed-user' and value['fixture_only'] is False and value['bindings']==expected and value['owner_uid']==uid,'qualification_actual_full_case_required')
    require(value['session']=={'User':str(uid),'Active':'yes','Remote':'no','LockedHint':'no','Type':'wayland','Class':'user','State':'active','Service':'gdm-password'},'qualification_actual_installed_gdm_session_required')
    require(all(type(value[key]) is int and value[key]==0 for key in ('runner_exit','postconditions_exit')) and isinstance(value['boot_id'],str) and re.fullmatch('[a-f0-9-]{36}',value['boot_id']) and isinstance(value['root_uuid'],str) and value['root_uuid'],'qualification_actual_full_case_exit')
    require(isinstance(value['artifacts'],dict) and set(value['artifacts'])=={'execution','postconditions','ui_capture'},'qualification_actual_case_artifacts_required')
    for name,reference in value['artifacts'].items():
        require(isinstance(reference,dict) and set(reference)=={'filename','sha256'} and reference['filename']==case+'-'+name+('.png' if name=='ui_capture' else '.json'),'qualification_case_artifact_path')
        data=private_metadata(CONTEXT/reference['filename'],maximum=16*1024**2)
        require(sha(data)==reference['sha256'],'qualification_case_artifact_changed')
        if name=='ui_capture':require(data[:8]==b'\x89PNG\r\n\x1a\n','qualification_actual_native_capture_required')
        else:
            observed=_strict(data)
            require(isinstance(observed,dict) and observed.get('bindings')==expected and observed.get('case')==case and observed.get('owner_uid')==uid,'qualification_actual_case_artifact_binding')
            require(observed.get('observations')==value['observations'][name],'qualification_case_summary_differs')
    return value


def valid_hash(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def valid_inventory(value,release):
    return isinstance(value,dict) and set(value)=={row['name'] for row in release['packages']} and all(item is None or isinstance(item,str) and re.fullmatch('[0-9][A-Za-z0-9.+:~_-]{0,95}',item) for item in value.values())


def helper_result(value,uid,release,code,*,installed=True):
    wanted={row['name']:row['version'] for row in release['packages']}
    expected=code.get('files',{}).get(HELPER)
    require(valid_hash(expected),'qualification_actual_helper_binding_required')
    require(value.get('helper_sha256')==expected and type(value.get('exit')) is int and value.get('executable')==HELPER and value.get('authenticated_uid')==uid and value.get('action')=='install' and value.get('exit')==0 and value.get('state')==('installed' if installed else 'canceled'),'qualification_actual_helper_result_required')
    require(isinstance(value.get('operation_id'),str) and re.fullmatch('[a-f0-9]{32}',value['operation_id']) and value.get('journal_operation_id')==value['operation_id'] and value.get('journal_state')==value['state'],'qualification_actual_operation_required')
    if installed:require(value.get('inventory_after')==wanted and value.get('postcondition_hashes')==release['postconditions'],'qualification_exact_installed_effect_required')


def validate_case(case,value,uid,release):
    require(case in CASES,'qualification_unknown_full_case')
    code=value['bindings']['code_pins']
    observation=value['observations'];require(set(observation)=={'execution','postconditions'},'qualification_case_observation_scope')
    execution=observation['execution'];post=observation['postconditions']
    require(isinstance(execution,dict) and isinstance(post,dict),'qualification_case_observations_required')
    if case=='install':
        helper_result(execution,uid,release,code)
        require(valid_inventory(post.get('inventory_before'),release) and all(item is None for item in post['inventory_before'].values()) and type(post.get('production_dispatches')) is int and post['production_dispatches']==1 and type(post.get('native_writes')) is int and post['native_writes']==1,'qualification_actual_fresh_production_dispatch_required')
        require(post.get('ui_backend')=='native-gtk4' and post.get('app_id')=='io.github.markaraujo.Toddy' and post.get('agent_absent_before') is True and post.get('consent_initially_unchecked') is True and post.get('explicit_terms_accepted') is True and post.get('polkit_action')=='io.github.markaraujo.Toddy.AcquireNative' and post.get('actual_owner_authentication')=='polkit-pam','qualification_actual_absent_agent_ui_required')
        require(all(isinstance(post.get(key),dict) and set(post[key])=={'user_agent','root_executor','local_runtime'} and all(state in ('inactive','not-loaded','not-running') for state in post[key].values()) for key in ('services_before','services_after')) and post.get('sensitive_state_before')==post.get('sensitive_state_after') and isinstance(post.get('sensitive_state_before'),dict) and set(post['sensitive_state_before'])=={'root_grant','provider_connections','keyring_metadata','model_metadata'} and post['sensitive_state_before']['root_grant'] is None and all(item is None or valid_hash(item) for item in post['sensitive_state_before'].values()),'qualification_no_automatic_activation_required')
    elif case=='stop':
        require(execution.get('action')=='cancel' and execution.get('executable')==HELPER and execution.get('authenticated_uid')==uid and execution.get('exit')==0 and execution.get('cancellation_requested') is True,'qualification_actual_stop_required')
        require(valid_inventory(post.get('inventory_before'),release) and valid_inventory(post.get('inventory_after'),release) and valid_hash(post.get('dpkg_before')) and valid_hash(post.get('dpkg_after')) and post.get('ui_busy_after') is False,'qualification_actual_safe_stop_required')
        if post.get('boundary')=='before_write':
            require(post.get('state')=='canceled' and post.get('write_intent_recorded') is False and post['inventory_before']==post['inventory_after'] and post['dpkg_before']==post['dpkg_after'],'qualification_actual_safe_stop_required')
        elif post.get('boundary')=='after_completed_write':
            require(post.get('state')=='installed' and post.get('write_intent_recorded') is True and post['inventory_after']=={row['name']:row['version'] for row in release['packages']} and post.get('postcondition_hashes')==release['postconditions'] and type(post.get('native_writes')) is int and post['native_writes']==1 and post.get('committed_effects_preserved') is True,'qualification_actual_committed_stop_required')
        else:raise SetupError('qualification_actual_stop_boundary_required')
    elif case=='reconnect':
        helper_result(execution,uid,release,code)
        require(post.get('reply_lost_after_native_write') is True and post.get('cursor_after_disconnect') in ('authorizing','outcome_unknown') and post.get('new_install_blocked_before_reconcile') is True and post.get('explicit_reconcile') is True and post.get('operation_id_before')==execution['operation_id']==post.get('operation_id_after') and type(post.get('install_submissions')) is int and post['install_submissions']==1 and type(post.get('native_writes')) is int and post['native_writes']==1 and valid_hash(post.get('package_state_after_write')) and post.get('package_state_after_write')==post.get('package_state_after_reconcile') and post.get('ui_reconnected_state')=='installed','qualification_actual_reconnect_no_replay_required')
    elif case=='tamper':
        require(execution.get('action')=='review' and execution.get('state')=='unavailable' and execution.get('reason') in ('release_signature','release_terms','release_qualification','no_verified_native_release'),'qualification_actual_signed_tamper_refusal_required')
        require(all(valid_hash(post.get(key)) for key in ('original_restored_sha256','original_sha256','journal_before','journal_after','dpkg_before','dpkg_after')) and post.get('tampered_file') in ('releases.json','releases.json.asc','qualifications') and post.get('original_restored_sha256')==post.get('original_sha256') and post.get('root_submissions')==0 and post.get('journal_before')==post.get('journal_after') and post.get('dpkg_before')==post.get('dpkg_after'),'qualification_actual_tamper_no_effect_required')
    elif case=='offline':
        require(execution.get('action')=='install' and execution.get('executable')==HELPER and execution.get('authenticated_uid')==uid and execution.get('state')=='deferred' and execution.get('write_intent_recorded') is False,'qualification_actual_offline_helper_required')
        require(valid_inventory(post.get('inventory_before'),release) and valid_inventory(post.get('inventory_after'),release) and valid_hash(post.get('dpkg_before')) and post.get('actual_network_or_fixed_repository_unavailable') is True and post.get('ui_state')=='deferred' and post.get('inventory_before')==post.get('inventory_after') and post.get('dpkg_before')==post.get('dpkg_after') and post.get('automatic_retry_count')==0,'qualification_actual_offline_no_effect_required')
    elif case=='lifecycle':
        require(execution.get('authority') in ('explicit-owner-executor-package-operation','explicit-authenticated-native-admin') and execution.get('actions')==['upgrade','remove','reinstall'] and execution.get('upgrade_exit')==execution.get('remove_exit')==0,'qualification_actual_package_lifecycle_required')
        helper_result(post.get('reinstall',{}),uid,release,code)
        require(valid_hash(post.get('private_state_before')) and post.get('initial_install_operation_id') is not None and execution.get('upgrade_version')==post.get('artifact2_version') and post.get('version_after_upgrade')==post.get('artifact2_version') and post.get('removed_package_absent') is True and post.get('private_state_before')==post.get('private_state_after') and post.get('actual_recovery_observation')=='original-closure-restored-new-explicit-operation' and post['reinstall']['operation_id']!=post.get('initial_install_operation_id') and post.get('fresh_setup_ui_after_recovery')=='packages_present' and post.get('automatic_activation_count')==0,'qualification_actual_lifecycle_recovery_required')
    return True


def lifecycle_artifact(release,case,catalog):
    """Real signed revision2 archive/record; never synthesize a version/status."""
    base=CONTEXT/'lifecycle-artifact2';descriptor=read(base/'artifact.json')
    require(set(descriptor)=={'name','version','architecture','record','archive','primary_record','primary_archive'} and descriptor['name'] in {row['name'] for row in release['packages']} and descriptor['architecture'] in ('amd64','all'),'qualification_actual_artifact2_required')
    require(isinstance(descriptor['version'],str) and payload.VERSION.fullmatch(descriptor['version']),'qualification_artifact2_version')
    stem=descriptor['name']+'_'+descriptor['version']+'_'+descriptor['architecture']
    require(descriptor['record']==stem+'.json' and descriptor['archive']==stem+'.deb' and descriptor['primary_record'].endswith('.json'),'qualification_artifact2_path')
    record=base/descriptor['record'];archive=base/descriptor['archive']
    secured(record,32*1024**2);secured(archive,2*1024**3)
    component=payload.component_from_record(record,base)
    primary=next(row for row in release['packages'] if row['name']==descriptor['name'])
    require(descriptor['architecture']==primary['architecture'] and payload.version_satisfies(descriptor['version'],'>',primary['version']),'qualification_actual_second_version_required')
    primary_stem=primary['name']+'_'+primary['version']+'_'+primary['architecture']
    require(descriptor['primary_archive']==primary_stem+'.deb' and descriptor['primary_record']==primary_stem+'.json','qualification_primary_artifact_path')
    old=base/descriptor['primary_archive'];secured(old,2*1024**3);secured(base/descriptor['primary_record'],32*1024**2)
    original=payload.component_from_record(base/descriptor['primary_record'],base)
    require(payload.digest(old)==primary['sha256'],'qualification_primary_archive_changed')
    control,contents,_=payload.archive_contents(old);require(control.get('Version')==primary['version'] and control.get('Package')==primary['name'],'qualification_primary_archive_identity')
    control2,contents2,_=payload.archive_contents(archive)
    # A project packaging revision can update its package documentation/index;
    # upstream/runtime/executable/unit/copyright bytes stay frozen.
    documentary='/usr/share/doc/'+primary['name']+'/'
    require({path:row for path,row in contents.items() if not path.startswith(documentary)}=={path:row for path,row in contents2.items() if not path.startswith(documentary)} and original['sources']==component['sources'] and original['copyright']==component['copyright'] and {key:value for key,value in control.items() if key not in ('Version','Installed-Size')}=={key:value for key,value in control2.items() if key not in ('Version','Installed-Size')},'qualification_artifact2_runtime_code_changed')
    for leaf in ('archive-keyring.gpg','Release','Release.gpg','Packages'):secured(base/leaf,16*1024**2)
    require(payload.digest(base/'archive-keyring.gpg')==catalog.keyring_sha256 and signature(base/'archive-keyring.gpg',base/'Release.gpg',base/'Release')==catalog.fingerprint,'qualification_artifact2_signature')
    trust=payload.ReleaseTrust(keyring=base/'archive-keyring.gpg',expected_key_sha256=catalog.keyring_sha256,
        release=base/'Release',signature=base/'Release.gpg',packages=base/'Packages',index_path='Packages')
    trust.verify([{**component,'archive':descriptor['archive'],'archive_bytes':archive.stat().st_size}])
    post=case['observations']['postconditions']
    require(post.get('artifact2_sha256')==component['archive_sha256'] and post.get('artifact2_version')==descriptor['version'] and case['observations']['execution'].get('upgrade_package')==descriptor['name'],'qualification_actual_artifact2_effect_binding')
    return {'name':descriptor['name'],'version':descriptor['version'],'archive_sha256':component['archive_sha256'],
        'record_sha256':component['component_record_sha256'],'signed_release_sha256':payload.digest(base/'Release')}


def assemble(release_id):
    marker=guard();catalog=NativeCatalog.load()
    require(release_id in catalog.releases and catalog.levels[release_id]=='native-components','qualification_actual_signed_preview_required')
    expected=bindings(catalog,release_id);release=catalog.releases[release_id]
    cases={name:load_case(name,expected,marker['owner_uid']) for name in CASES}
    for name,value in cases.items():validate_case(name,value,marker['owner_uid'],release)
    artifact2=lifecycle_artifact(release,cases['lifecycle'],catalog)
    local={}
    if any(row['name']=='llama-cpp' for row in release['packages']):
        # Existing real component evidence may support only these same local
        # compatibility checks, never any of the new production full-flow cases.
        row=next(row for row in catalog.value['releases'] if row['id']==release_id)
        report=read(catalog.directory/'qualifications'/(row['qualification_sha256']+'.json'))
        evidence=read(catalog.directory/'qualifications'/(report['retained_evidence_sha256']+'.evidence.json'))
        cpu=evidence.get('native_cpu_denial')
        require(isinstance(cpu,dict) and cpu.get('native_result')=='denied_before_apt' and cpu.get('native_command_calls')==0 and cpu.get('code_pins')==expected['code_pins'] and cpu.get('trust_pins')==expected['trust_pins'] and cpu.get('package_set_sha256')==expected['package_set_sha256'],'qualification_actual_local_cpu_evidence_required')
        sys.path.insert(0,str(Path(__file__).parent))
        from native_acquisition_component import validate_cpu_receipt
        from types import SimpleNamespace
        validate_cpu_receipt(cpu,SimpleNamespace(code=expected['code_pins'],trust=expected['trust_pins'],release=release,revision=cpu['candidate_sha256']))
        local={'component_qualification_sha256':row['qualification_sha256'],'native_cpu_denial':cpu}
    catalog.ensure_current();active(marker['owner_uid'])
    evidence={'version':1,'scope':'installed-native-agent-acquisition','environment':'native-installed-user','fixture_only':False,
        'qualification_level':'native-full-flow','runner_exit':0,'postconditions_exit':0,**expected,
        'cases':cases,'lifecycle_artifact2':artifact2,'local_supporting_component_evidence':local,
        'assembler_sha256':payload.digest(__file__)}
    report={'version':1,'scope':'installed-native-agent-acquisition','native_result':'passed','qualification_level':'native-full-flow',
        'package_set_sha256':expected['package_set_sha256'],'code_pins':expected['code_pins'],'trust_pins':expected['trust_pins'],
        'checks':{name:True for name in REQUIRED_CHECKS|(LOCAL_CHECKS if local else set())},
        'retained_evidence_sha256':sha(_encode(evidence)+b'\n')}
    # Read-only: parent retains exact canonical bytes, reviews and separately
    # signs/seals. No catalog or prior report is overwritten here.
    return {'retained_evidence':evidence,'qualification':report,'publication_performed':False}


def main():
    require(sys.argv[1:] and len(sys.argv)==2,'qualification_release_argument_required')
    print(json.dumps(assemble(sys.argv[1]),sort_keys=True,separators=(',',':')))


if __name__=='__main__':main()
