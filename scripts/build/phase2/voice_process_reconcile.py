"""Fixed native2 readonly process retry/catalog producer; frozen voice driver stays intact."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import voice_native as frozen
import offline_payload as archive_payload
import pipewire_tools_native as transport_native

R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
FROZEN_DRIVER='5a1dc85c634e2c54edad42f94c7222ef5fba56331aadc5efbb849178474c6dee'
GENERATION='native2';JOB='voice-process-native2-r1';PREFIX=L/JOB
WORK=T/'sources/phase2/work'/JOB
PACKAGE='toddy-voice-native-catalog';VERSION='0.2.0-1+toddy1'
INSTALL_RECIPE='scripts/build/phase2/voice_reconcile_install.sh'
OLD_PIPEWIRE_ARCHIVE='6fcccccb584101ebf0899dcabbc64ff8551f8cc4e58356bc8878febc6a17c56a'
OLD_PIPEWIRE_RECORD='ebdad900696ab299bcc7be52dcbde490c0a2a6d5afb3b659acb89cb6c2a77303'
FAILED_PIPEWIRE_ARCHIVE='bf08b0426e4596eed1363fb2a64889ab31b4ecafdb58bc3f92ebb5d91a915a55'
FAILED_PIPEWIRE_RECORD='8302491a6fae68d1a443b33e8d9bd884be19719520fb89de9e693da56b4d9c3c'
FAILED_PIPEWIRE_RECEIPT='994c633373d1c15ded40075c6ff1320da5bef78eb4aa44a4d9d1fe533b842cc6'
FAILED_PIPEWIRE_MANIFEST='4166be95d52f06a4b623d0d89b0765c6d127c40f765e44417c8a833097c14f58'


def file(suffix):return Path(str(PREFIX)+'.'+suffix)
def read(path):return frozen.read(path)
def digest(path):return frozen.digest(path)
def write(path,value):return frozen.write_new(path,value)
def producer_pins():return {'producer':digest(Path(__file__)),'frozen_driver':digest(HERE/'voice_native.py'),'job':digest(HERE/'job.py'),'harness':digest(HERE/'isolated.sh'),'install_recipe':digest(R/INSTALL_RECIPE)}


def installed_components():
    if digest(HERE/'voice_native.py')!=FROZEN_DRIVER:raise ValueError('Exact unchanged native2 voice driver required')
    records={};bindings={}
    for name in frozen.COMPONENTS:
        source,work,prefix,value=frozen.prepared(name,GENERATION)
        path,record=frozen.native_record(name);checked=read(Path(str(prefix)+'.checked.json'))
        audit=frozen.require_write_audit(prefix,'install',inputs=frozen.install_inputs(prefix,value),record_sha256=digest(path))
        if checked['record_sha256']!=digest(path) or checked['native_write_audit_sha256']!=audit:raise ValueError('Actual native2 installed/check/audit proof changed')
        records[name]=(path,record)
        bindings[name]={'prepared_sha256':digest(Path(str(prefix)+'.prepared.json')),'qualified_sha256':digest(Path(str(prefix)+'.qualified.json')),'checked_sha256':digest(Path(str(prefix)+'.checked.json')),'install_audit_sha256':audit,'record_sha256':digest(path)}
    for name in ('pipewire','wireplumber','toddy-voice','pipewire-audio-tools'):records[name]=frozen.native_record(name)
    if records['pipewire'][1]['version']!='1.6.8-1+toddy1' or records['pipewire-audio-tools'][1]['version']!='1.6.8-1+toddy1' or records['wireplumber'][1]['version']!='0.5.15-1+toddy1' or records['toddy-voice'][1]['version']!='0.2.0-1+toddy1':raise ValueError('Exact restored PipeWire1 plus separate audio tools and unchanged controller required')
    bindings['pipewire-transport']=transport_proof(records)
    return records,bindings


def full_root_success(step,recipe,check):
    base=Path('/var/log/toddy/build')/step
    path=base.with_suffix('.success.json');value=read(path)
    if (value.get('step')!=step or any(type(value.get(key)) is not int or value[key]!=0 for key in ('recipe_exit','postcheck_exit')) or
            value.get('recipe_sha256')!=digest(HERE/recipe) or value.get('postcheck_sha256')!=digest(HERE/check) or
            value.get('runner_sha256')!=digest(HERE.parent/'run_step.py') or base.with_suffix('.failed.json').exists() or base.with_suffix('.running.json').exists()):raise ValueError('Actual separate transport full-root transaction success required')
    log=base.with_suffix('.log');frozen.regular(log)
    if value.get('log_sha256')!=digest(log):raise ValueError('Actual native transport log custody required')
    manifest=base.with_suffix('.manifest.json');frozen.regular(manifest);changes=read(manifest)
    if not isinstance(changes,dict) or type(value.get('changed_paths')) is not int or len(changes)!=value['changed_paths']:raise ValueError('Actual full-root transport mutation evidence required')
    return {'success_sha256':digest(path),'manifest_sha256':digest(manifest)},changes


def transport_proof(records):
    # The failed revision2 installation is historical failure, never renamed or
    # reinterpreted as success. Two NEW controlled transactions follow it.
    failed=Path('/var/log/toddy/build/b09-pipewire-tools-1.failed.json');frozen.regular(failed);failure=read(failed)
    if digest(failed)!=FAILED_PIPEWIRE_RECEIPT or digest(failed.with_name('b09-pipewire-tools-1.manifest.json'))!=FAILED_PIPEWIRE_MANIFEST:raise ValueError('Exact retained failed PipeWire2 audit pins required')
    if failure.get('step')!='b09-pipewire-tools-1' or failure.get('recipe_sha256')!=digest(HERE/'pipewire_tools_install.sh') or failure.get('postcheck_sha256')!=digest(HERE/'pipewire_tools_check.sh') or type(failure.get('recipe_exit')) is not int or failure['recipe_exit']!=0 or type(failure.get('postcheck_exit')) is not int or failure['postcheck_exit']!=1 or failed.with_name('b09-pipewire-tools-1.success.json').exists():raise ValueError('Retained actual PipeWire2 failed postcheck required')
    old=Path('/var/log/toddy/packages/pipewire_1.6.8-1+toddy1_amd64.json')
    if digest(old)!=OLD_PIPEWIRE_RECORD or digest(records['pipewire'][0])!=OLD_PIPEWIRE_RECORD:raise ValueError('Exact original PipeWire record must actually be restored')
    frozen.verify_package_record(read(old),T)
    restore,removed=full_root_success('b09-pipewire-base-restore-1','pipewire_base_restore_install.sh','pipewire_base_restore_check.sh')
    tools,added=full_root_success('b09-pipewire-audio-tools-1','pipewire_audio_tools_install.sh','pipewire_audio_tools_check.sh')
    revision2=Path('/var/log/toddy/packages/pipewire_1.6.8-1+toddy2_amd64.json');revision2_archive=Path('/var/cache/toddy/packages/pipewire_1.6.8-1+toddy2_amd64.deb')
    frozen.regular(revision2);frozen.regular(revision2_archive);rejected=read(revision2)
    control,body,_=archive_payload.archive_contents(revision2_archive)
    if digest(revision2)!=FAILED_PIPEWIRE_RECORD or digest(revision2_archive)!=FAILED_PIPEWIRE_ARCHIVE or rejected.get('archive_sha256')!=FAILED_PIPEWIRE_ARCHIVE or control.get('Package')!='pipewire' or control.get('Version')!='1.6.8-1+toddy2' or rejected.get('payload')!=body:raise ValueError('Retained exact rejected PipeWire2 archive/record required')
    additions=set(body)-set(read(old)['payload'])
    if len(additions)!=11 or any(body.get(name)!=row for name,row in read(old)['payload'].items()):raise ValueError('Exact rejected eleven additions and unchanged old payload required')
    restored=read(L/'pipewire-base-restore-1.json');installed=read(L/'pipewire-audio-tools-install-1.json')
    if restored.get('state')!='native-pipewire-base-restored' or installed.get('state')!='native-audio-tools-package-verified' or installed.get('old_library_payload_unchanged') is not True:raise ValueError('Actual controlled base restoration and separate tools receipts required')
    upgrade=restored.get('failed_upgrade',{})
    if (restored.get('old_archive_sha256')!=OLD_PIPEWIRE_ARCHIVE or restored.get('old_record_sha256')!=OLD_PIPEWIRE_RECORD or restored.get('old_payload_unchanged') is not True or type(restored.get('apt_check_exit')) is not int or restored['apt_check_exit']!=0 or
            restored.get('added_paths_absent')!=sorted(additions) or
            upgrade!={'step':'b09-pipewire-tools-1','failed_receipt_sha256':digest(failed),'manifest_sha256':digest(failed.with_name('b09-pipewire-tools-1.manifest.json')),'archive_sha256':FAILED_PIPEWIRE_ARCHIVE,'record_sha256':digest(revision2)} or
            any(removed.get(name,{}).get('after','MISSING') is not None for name in additions)):
        raise ValueError('Actual exact restored archive/failed upgrade/eleven removals/APT proof required')
    expected_sources={'scripts/build/phase2/'+name for name in ('pipewire_base_restore.py','pipewire_base_restore_install.sh','pipewire_base_restore_check.sh')}
    if restored.get('source_inputs')!={name:digest(R/name) for name in expected_sources}:raise ValueError('Actual controlled restoration source pins required')
    transport=T/'usr/bin/pw-cat';frozen.regular(transport)
    expected=records['pipewire-audio-tools'][1]['payload'].get('/usr/bin/pw-cat',{}).get('sha256')
    tooling=installed.get('manifest',{});prepared,compiled,closure=transport_native.qualify()
    restoration={'step':'b09-pipewire-base-restore-1',**restore,'receipt_sha256':digest(L/'pipewire-base-restore-1.json'),
        'failed_upgrade':upgrade,'old_archive_sha256':OLD_PIPEWIRE_ARCHIVE,'old_record_sha256':OLD_PIPEWIRE_RECORD}
    if (type(installed.get('apt_check_exit')) is not int or installed['apt_check_exit']!=0 or installed.get('actual_audio_process_qualification')!='pending' or
            installed.get('restoration_receipt_sha256')!=restoration['receipt_sha256'] or installed.get('new_record_sha256')!=digest(records['pipewire-audio-tools'][0]) or installed.get('new_archive_sha256')!=records['pipewire-audio-tools'][1]['archive_sha256'] or installed.get('native_pwcat_sha256')!=expected or
            tooling.get('restoration')!=restoration or tooling.get('baseline_archive_sha256')!=OLD_PIPEWIRE_ARCHIVE or tooling.get('baseline_record_sha256')!=OLD_PIPEWIRE_RECORD or tooling.get('frozen_source_sha256')!=transport_native.SOURCE_SHA or
            tooling.get('prepared_sha256')!=digest(transport_native.PREPARED) or tooling.get('build_job_sha256')!=digest(transport_native.LOG/(transport_native.JOB+'.job.json')) or tooling.get('build_exit_sha256')!=digest(transport_native.LOG/(transport_native.JOB+'.exit')) or tooling.get('compiled_stage')!=compiled or tooling.get('direct_elf_closure')!=closure):
        raise ValueError('Actual unchanged compile2/restoration/separate owned tools source proof required')
    source_inputs=tooling.get('source_inputs',{})
    minimum={'scripts/build/phase2/pipewire_audio_tools_install.sh','scripts/build/phase2/pipewire_audio_tools_check.sh','scripts/build/phase2/pipewire_base_restore.py'}
    if not isinstance(source_inputs,dict) or not minimum<=set(source_inputs):raise ValueError('Actual tools producer source closure required')
    for name,sha in source_inputs.items():
        archive_payload.canonical(name,absolute=False)
        if not name.startswith('scripts/build/') or Path(name).suffix not in ('.py','.sh') or not isinstance(sha,str) or not archive_payload.HASH.fullmatch(sha) or digest(R/name)!=sha:raise ValueError('Actual tools source bytes changed')

    if not expected or expected!=digest(transport) or added.get('/usr/bin/pw-cat',{}).get('after',{}).get('sha256')!=expected or removed.get('/usr/bin/pw-cat',{}).get('after') is not None:raise ValueError('Actual restored absence then new owned native pw-cat required')
    return {'failed_revision2_sha256':digest(failed),'failed_revision2_archive_sha256':FAILED_PIPEWIRE_ARCHIVE,'restore':restore,'tools':tools,
        'restore_receipt_sha256':digest(L/'pipewire-base-restore-1.json'),
        'tools_receipt_sha256':digest(L/'pipewire-audio-tools-install-1.json'),
        'record_sha256':digest(records['pipewire-audio-tools'][0]),'base_record_sha256':digest(old)}


def old_failure(source,prefix):
    exit_path=Path(str(prefix)+'.process.exit.json');marker=Path(str(prefix)+'.process.json');exit=read(exit_path)
    expected=['bash',str(R/'scripts/build/phase2/isolated.sh'),str(source),str(T/'sources/phase2/work/voice-whisper-cpp-native2'),'python3','/src/qualification/process-check.py']
    if type(exit.get('exit')) is not int or exit['exit']==0 or exit.get('command')!=expected or exit.get('prepared_sha256')!=digest(Path(str(prefix)+'.prepared.json')):raise ValueError('Exact retained failed readonly process2 required')
    return {'exit_sha256':digest(exit_path),'marker_sha256':digest(marker),'log_sha256':digest(Path(str(prefix)+'.process.log'))}


def context():
    value=read(file('prepared.json'));records,bindings=installed_components()
    source,_,prefix,prepared=frozen.prepared('whisper-cpp',GENERATION)
    if value['producer_pins']!=producer_pins() or value['bindings']!=bindings or value['records']!={name:digest(path) for name,(path,_) in records.items()} or value['old_failed_process']!=old_failure(source,prefix):raise ValueError('Retry source/native/audit/failure pins changed')
    return value,source,records


def prepare():
    if os.path.lexists(WORK) or list(L.glob(JOB+'.*')):raise ValueError('Inspect existing retry generation; no replay')
    records,bindings=installed_components();source,_,prefix,prepared=frozen.prepared('whisper-cpp',GENERATION)
    failure=old_failure(source,prefix);frozen.reserve(64*1024**2)
    write(file('intent.json'),{'scope':'NEW readonly real process retry only; old failure retained','producer_pins':producer_pins(),'bindings':bindings,'old_failed_process':failure})
    WORK.mkdir(mode=0o755);os.chown(WORK,101,101)
    write(file('prepared.json'),{'version':1,'generation':GENERATION,'job':JOB,'work':str(WORK),'source':str(source),'producer_pins':producer_pins(),'bindings':bindings,'records':{name:digest(path) for name,(path,_) in records.items()},'old_failed_process':failure,'prepared_whisper_sha256':digest(Path(str(prefix)+'.prepared.json'))})


def process_command(source):return ['/bin/bash',str(HERE/'isolated.sh'),str(source),str(WORK),'python3','/src/qualification/process-check.py']


def validate_process(value,*,runtime_files,transport_files):
    if type(value.get('tests_run')) is not int or value['tests_run']<3 or any(type(value.get(key)) is not int or value[key]!=0 for key in ('failures','errors','skipped')) or value.get('files')!=runtime_files:raise ValueError('Actual complete native process tests/runtime pins required')
    sessions=value.get('file_sessions',{})
    if set(sessions)!={'en','pt-BR'} or value.get('native_engine_stop',{}).get('code')!='canceled':raise ValueError('Actual bilingual native inference/engine Stop required')
    for row in sessions.values():
        error=row.get('word_error_rate')
        if not isinstance(row.get('transcript'),str) or not row['transcript'].strip() or type(error) not in (float,int) or not math.isfinite(error) or not 0<=error<=.4:raise ValueError('Actual nonempty native transcript/WER required')
    transport=value.get('transport',{})
    if set(transport)!=set(transport_files) or any(transport[name].get('sha256')!=sha for name,sha in transport_files.items()):raise ValueError('Actual fixed native transport help proof changed')


def qualified_process():
    prepared,source,records=context()
    exit_path=Path(str(PREFIX)+'.exit');job_path=Path(str(PREFIX)+'.job.json');job=read(job_path)
    if exit_path.read_text().strip()!='0' or job.get('command')!=process_command(source) or job.get('harness_sha256')!=prepared['producer_pins']['harness']:raise ValueError('Actual NEW retry job/command/exit0 required')
    path=WORK/'process-qualified.json';value=read(path)
    runtime={name:digest(T/'usr/lib/toddy/voice'/name) for name in ('process.py','child.py','artifacts.py','session.py')}
    for name,sha in runtime.items():
        if digest(source/'qualification/process-runtime/runtime/voice'/name)!=sha:raise ValueError('Installed runtime differs from immutable test source')
    transport={name:digest(T/path.lstrip('/')) for name,path in [('capture','/usr/lib/toddy/voice/pw-record'),('playback','/usr/lib/toddy/voice/pw-play'),('device-list','/usr/bin/pw-dump'),('pw-cat','/usr/bin/pw-cat')]}
    validate_process(value,runtime_files=runtime,transport_files=transport)
    return {'version':1,'kind':'actual-native2-process-retry-v1','producer_pins':producer_pins(),'prepared_sha256':digest(file('prepared.json')),'old_failed_process':prepared['old_failed_process'],'job_sha256':digest(job_path),'job_exit_sha256':digest(exit_path),'process_sha256':digest(path),'records':prepared['records'],'scope':'Actual new file-only/process/transport-help proof; physical/device/PTT/GNOME remains separate'},value,records


def process():
    prepared,source,_=context()
    # job.py independently writes the actual command, native log and exit. No
    # old success marker/exit is copied, synthesized, renamed or overwritten.
    result=subprocess.run([sys.executable,str(HERE/'job.py'),JOB,str(source),str(WORK),'python3','/src/qualification/process-check.py'],check=True)
    proof,_,_=qualified_process();write(file('process-validated.json'),proof)


def catalog_data(process,records):
    versions={'pipewire':'1.6.8','wireplumber':'0.5.15','whisper-cpp':'1.9.5','espeak-ng':'1.52.0'}
    specs=[('capture','/usr/lib/toddy/voice/pw-record','0.2.0','https://github.com/markaraujo/toddy-os','MIT','/usr/share/doc/toddy-voice/copyright'),('playback','/usr/lib/toddy/voice/pw-play','0.2.0','https://github.com/markaraujo/toddy-os','MIT','/usr/share/doc/toddy-voice/copyright'),('device-list','/usr/bin/pw-dump','1.6.8',records['pipewire'][1]['sources'][0]['url'],'MIT','/usr/share/doc/pipewire/copyright'),('stt-engine','/usr/bin/whisper-cli','1.9.5',records['whisper-cpp'][1]['sources'][0]['url'],'MIT','/usr/share/doc/whisper-cpp/VOICE-LICENSES.txt'),('stt-model','/usr/share/toddy/voice/models/ggml-base.bin',frozen.COMPONENTS['toddy-voice-model-base'][1].split('-1+toddy',1)[0],records['toddy-voice-model-base'][1]['sources'][0]['url'],'MIT','/usr/share/doc/toddy-voice-model-base/whisper-original-license.txt'),('tts-engine','/usr/bin/espeak-ng','1.52.0',records['espeak-ng'][1]['sources'][0]['url'],'LicenseRef-eSpeak-NG-per-file','/usr/share/doc/espeak-ng/VOICE-LICENSES.txt')]
    artifacts={spec[0]:frozen.artifact(*spec) for spec in specs}
    for role,leaf in (('capture','pw-record'),('playback','pw-play')):
        if artifacts[role]['sha256']!=digest(R/'runtime/voice/wrappers'/leaf):raise ValueError('Reviewed fixed wrapper bytes required')
    transport=T/'usr/bin/pw-cat';info=frozen.regular(transport)
    return {'voice_catalog_version':1,'status':'native-qualified','tts_engine':'espeak-ng','native_dependencies':{name:{'version':version,'component_record_sha256':digest(records[name][0])} for name,version in versions.items()},'process_control':{'launcher_sha256':process['files']['child.py'],'runner_sha256':process['files']['process.py'],'pw_cat_sha256':digest(transport),'pw_cat_bytes':info.st_size,'evidence_sha256':digest(WORK/'process-qualified.json')},'artifacts':artifacts}


def preview_command():
    code="import sys;sys.path.insert(0,'/usr/lib');from toddy.voice.catalog import NativeVoiceCatalog;v=NativeVoiceCatalog().preview();assert v['languages']==['en','pt-BR'] and not v['always_listening'] and not v['automatic_download']"
    return ['chroot','--userspec=101:101','--groups=101',str(T),'/usr/bin/env','-i','HOME=/tmp','PATH=/usr/bin:/usr/sbin','LC_ALL=C','/usr/bin/python3','-I','-c',code]


def catalog(lease):
    proof,process,records=qualified_process()
    if proof!=read(file('process-validated.json')):raise ValueError('Actual retry qualification changed')
    value=catalog_data(process,records);destination=T/'usr/share/toddy/voice/catalog.json';receipt=file('catalog.json')
    if os.path.lexists(destination) or receipt.exists():raise ValueError('Preserve prior catalog; no update/replay')
    command=preview_command();inputs={'producer_pins':producer_pins(),'process_validation_sha256':digest(file('process-validated.json')),'process_sha256':proof['process_sha256'],'catalog_sha256':hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()}
    with frozen.native_write_audit(PREFIX,'catalog',command,inputs,lease) as audit:
        destination.parent.mkdir(parents=True,exist_ok=True);write(destination,value);destination.chmod(0o644)
        result=subprocess.run(command,check=True,timeout=30);audit['command_exit']=result.returncode;audit['postcheck_exit']=0
    write(receipt,{'version':1,'kind':'reconciled-native-voice-catalog-v1','catalog_sha256':digest(destination),'native_write_audit_sha256':frozen.require_write_audit(PREFIX,'catalog',inputs=inputs,command=command),'audit_prefix':str(PREFIX),'audit_inputs':inputs,'records':{name:digest(path) for name,(path,_) in records.items()},'producer_pins':producer_pins(),'process_validation_sha256':digest(file('process-validated.json')),'process_evidence_sha256':digest(WORK/'process-qualified.json'),'old_failed_process':proof['old_failed_process'],'scope':'Component/process/transport-help qualification only; no device/PTT/physical acceptance'})


def checked_catalog():
    value=read(file('catalog.json'))
    if value.get('kind')!='reconciled-native-voice-catalog-v1' or value.get('producer_pins')!=producer_pins() or value['native_write_audit_sha256']!=frozen.require_write_audit(PREFIX,'catalog',inputs=value['audit_inputs'],command=preview_command()) or value['catalog_sha256']!=digest(T/'usr/share/toddy/voice/catalog.json'):raise ValueError('Actual new catalog write audit required')
    for name,expected in value['records'].items():
        path,_=frozen.native_record(name)
        if digest(path)!=expected:raise ValueError('Catalog actual native package record changed')
    proof,_,_=qualified_process()
    if proof!=read(file('process-validated.json')) or value['process_evidence_sha256']!=proof['process_sha256']:raise ValueError('Actual retry process proof changed')
    return value


def install_catalog(lease):
    value=checked_catalog();stage=T/'sources/stage/toddy-voice-native-catalog-native2-r1'
    marker=file('catalog-package-intent.json')
    if stage.exists() or marker.exists():raise ValueError('Preserve catalog package intent/stage; no replay')
    if subprocess.run(['chroot',str(T),'dpkg-query','-W',PACKAGE],capture_output=True).returncode!=1:raise ValueError('Only first catalog package installation here')
    depends=[]
    for name in value['records']:
        _,record=frozen.native_record(name);depends.append(name+' (= '+record['version']+')')
    command=[sys.executable,str(R/'scripts/build/stage_package.py'),PACKAGE,VERSION,str(stage),'--architecture','all','--recipe',INSTALL_RECIPE,'--depends',', '.join(sorted(depends)),'--install']
    inputs={'producer_pins':producer_pins(),'catalog_receipt_sha256':digest(file('catalog.json')),'catalog_sha256':value['catalog_sha256']}
    frozen.reserve(16*1024**2)
    with frozen.native_write_audit(PREFIX,'catalog-package',command,inputs,lease) as audit:
        write(marker,{'state':'install-intended-no-replay','inputs':inputs})
        target=stage/'usr/share/toddy/voice/catalog.json';target.parent.mkdir(parents=True);shutil.copyfile(T/'usr/share/toddy/voice/catalog.json',target)
        doc=stage/'usr/share/doc'/PACKAGE;doc.mkdir(parents=True)
        for source,name in ((file('catalog.json'),'qualification.json'),(WORK/'process-qualified.json','process-qualified.json'),(file('process-validated.json'),'process-retry-validation.json')):shutil.copyfile(source,doc/name)
        for name in frozen.COMPONENTS:
            _,_,prefix,_=frozen.prepared(name,GENERATION);shutil.copyfile(Path(str(prefix)+'.qualified.json'),doc/(name+'-qualified.json'))
        for source,name in ((R/'tests/fixtures/voice/human/manifest.json','human-sample-attribution.json'),(R/'tests/fixtures/voice/human/README.md','human-samples.md'),(R/'LICENSE','MIT'),(R/'LICENSES/CC-BY-4.0.txt','CC-BY-4.0')):shutil.copyfile(source,doc/name)
        (doc/'copyright').write_bytes((R/'LICENSE').read_bytes()+b'\nQualification documentation:\n'+(R/'LICENSES/CC-BY-4.0.txt').read_bytes())
        result=subprocess.run(command,cwd=R,check=True);audit['command_exit']=result.returncode
        path,record=frozen.native_record(PACKAGE);audit['postcheck_exit']=0;audit['package_record_sha256']=digest(path)
    write(file('catalog-package-installed.json'),{'record_sha256':digest(path),'archive_sha256':record['archive_sha256'],'native_write_audit_sha256':frozen.require_write_audit(PREFIX,'catalog-package',inputs=inputs,command=command,record_sha256=digest(path)),'audit_inputs':inputs,'producer_pins':producer_pins()})


def check_catalog():
    checked_catalog();installed=read(file('catalog-package-installed.json'));path,record=frozen.native_record(PACKAGE)
    if installed['producer_pins']!=producer_pins() or installed['record_sha256']!=digest(path) or installed['native_write_audit_sha256']!=frozen.require_write_audit(PREFIX,'catalog-package',inputs=installed['audit_inputs'],record_sha256=digest(path)):raise ValueError('Actual controlled catalog package install proof required')
    subprocess.run(preview_command(),check=True,timeout=30)
    if subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip():raise ValueError('Actual dpkg audit must pass')
    subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
    write(file('catalog-package-checked.json'),{'record_sha256':digest(path),'catalog_sha256':digest(T/'usr/share/toddy/voice/catalog.json'),'install_audit_sha256':installed['native_write_audit_sha256'],'scope':'Owned optional catalog/process component proof only; GUI/PTT/device/physical evidence still separate'})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','process','catalog','install-catalog','check-catalog']);args=parser.parse_args()
    if os.getuid()!=0 or Path(__file__).resolve()!=R/'scripts/build/phase2/voice_process_reconcile.py':raise SystemExit('Designated native coordinator only')
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True);os.umask(0o022);os.environ['LC_ALL']='C'
    with Path('/var/log/toddy/build/voice-pipeline.lock').open('a') as pipeline:
        fcntl.flock(pipeline,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.phase=='process':process() # Existing isolated.sh owns global build lock.
        else:
            with frozen.BUILD_LOCK.open('a') as lease:
                fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
                if list(frozen.BUILD_LOCK.parent.glob('*.running.json')):raise ValueError('Another native writer remains unreconciled')
                if args.phase=='prepare':prepare()
                elif args.phase=='catalog':catalog(lease)
                elif args.phase=='install-catalog':install_catalog(lease)
                else:check_catalog()


if __name__=='__main__':main()
