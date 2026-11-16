"""Guarded native optional voice packages. No operation is safe to run on host.

Each generation is one-shot; inspect retained state after interruption. Build and
consumer jobs use the existing no-network read-only-input UID101 harness. A root
catalog requires a separate actual installed process-control qualification.
"""
import argparse,fcntl,hashlib,json,os,re,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

# Direct absolute script execution must resolve only these reviewed sibling
# helpers, including source_notices/locked_inputs used by package_copyright.
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import run_step as root_audit

from voice_inputs import digest,load_lock,verify_file,validate_members,patch_source
from verify_stage import inspect_stage

R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
BUILD_LOCK=Path('/var/log/toddy/build/build.lock')
RESERVE=16*1024**3+128*1024**2
COMPONENTS={'whisper-cpp':('whisper-source','1.9.5-1+toddy1','voice-whisper-build.sh','usr/bin/whisper-cli'),
 'espeak-ng':('espeak-source','1.52.0-1+toddy1','voice-espeak-build.sh','usr/bin/espeak-ng'),
 'toddy-voice-model-base':('whisper-base-model','5359861c739e955e79d9a303bcbc70fb988958b1-1+toddy1',None,'usr/share/toddy/voice/models/ggml-base.bin')}


def write_new(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def read(path):return json.loads(path.read_text())


def paths(component,generation):
    if component not in COMPONENTS or not re.fullmatch('[a-z0-9][a-z0-9-]{0,31}',generation):raise ValueError('voice_generation')
    key=f'voice-{component}-{generation}'
    return (T/'sources/phase2/inputs'/key,T/'sources/phase2/work'/key,L/key)


def reserve(extra=0):
    if shutil.disk_usage(T).free<RESERVE+extra:raise ValueError('voice_native_reserve')


def regular(path):
    for part in (path,*path.parents):
        info=part.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('voice_root_owned_path')
    info=path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ValueError('voice_regular_file')
    return info


def prepared(component,generation):
    source,work,prefix=paths(component,generation);value=read(Path(str(prefix)+'.prepared.json'))
    if value['component']!=component or value['generation']!=generation:raise ValueError('voice_prepared_identity')
    if inspect_stage(source)['manifest_sha256']!=value['source_manifest_sha256']:raise ValueError('voice_prepared_source_changed')
    if value['driver_sha256']!=digest(Path(__file__)) or value['harness_sha256']!=digest(R/'scripts/build/phase2/isolated.sh'):raise ValueError('voice_prepared_driver_changed')
    if COMPONENTS[component][2] and value['recipe_sha256']!=digest(R/'scripts/build/phase2'/COMPONENTS[component][2]):raise ValueError('voice_prepared_recipe_changed')
    return source,work,prefix,value


def audit_path(prefix,phase,suffix):
    if phase not in ('install','catalog','catalog-package'):raise ValueError('voice_write_audit_phase')
    return Path(str(prefix)+'.'+phase+'-audit.'+suffix)


def audit_pins():
    files={'driver':Path(__file__), 'snapshot_runner':Path(root_audit.__file__),'interpreter':Path(sys.executable).resolve()}
    for relative in ('scripts/build/stage_package.py','scripts/build/package_backend.py',
            'scripts/build/source_notices.py','scripts/build/locked_inputs.py',
            'scripts/build/package_ownership.py','scripts/build/provenance.py',
            'scripts/build/phase2/package_copyright.py','scripts/build/phase2/voice-install.sh',
            'config/sources.lock.json','config/books.lock.json','config/phase2/sources.lock.json',
            'config/component-licenses.json','config/package-ownership-policy.json',
            'runtime/voice/native-inputs.lock.json'):
        files[relative]=R/relative
    for relative in ('config/security-overlay.lock.json','config/supplemental-sources.lock.json'):
        if (R/relative).exists():files[relative]=R/relative
    return {name:digest(path) for name,path in files.items()}


@contextmanager
def native_write_audit(prefix,phase,command,inputs,lease):
    """Existing full-root dispatcher evidence under its already owned lock FD.

    This observes mutations; it is not install confinement or optimized-path
    qualification. Source/build scratch follows run_step's existing exclusions.
    No failed/partial generation can be retried or accepted as complete.
    """
    if lease is None or root_audit.TARGET!=T or BUILD_LOCK.is_symlink():raise ValueError('voice_write_audit_owned_lock_required')
    actual=os.fstat(lease.fileno());expected=BUILD_LOCK.stat()
    if (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino):raise ValueError('voice_write_audit_owned_lock_required')
    # Re-lock the SAME open description; no second fd or recursive dispatcher.
    fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if list(prefix.parent.glob(prefix.name+'.'+phase+'-audit.*')):raise ValueError('voice_write_audit_exists_inspect_no_replay')
    running=BUILD_LOCK.parent/(prefix.name+'.'+phase+'-audit.running.json')
    if list(BUILD_LOCK.parent.glob('*.running.json')):raise ValueError('voice_other_native_recipe_running')
    intent={'version':1,'phase':phase,'command':command,'inputs':inputs,'pins':audit_pins(),
        'pid':os.getpid(),'started_utc':datetime.now(timezone.utc).isoformat(),
        'snapshot_scope':['usr','etc','var','tools','lib64','boot'],
        'scope':'Existing run_step full-root build manifest; no native acceptance from source fixtures or optimized isolation qualification'}
    root_audit.write(audit_path(prefix,phase,'intent.json'),intent)
    root_audit.write(running,{**intent,'intent_path':str(audit_path(prefix,phase,'intent.json'))})
    before=root_audit.snapshot();root_audit.write(audit_path(prefix,phase,'before.json'),before)
    state={**intent,'command_exit':None,'postcheck_exit':None}
    failed=False
    try:
        yield state
    except BaseException as error:
        failed=True;state['error_type']=type(error).__name__
        if isinstance(error,subprocess.CalledProcessError):
            state['command_exit' if state['command_exit'] is None else 'postcheck_exit']=error.returncode
        raise
    finally:
        after=root_audit.snapshot();root_audit.write(audit_path(prefix,phase,'after.json'),after)
        changes={name:{'before':before.get(name),'after':after.get(name)} for name in sorted(before.keys()|after.keys()) if before.get(name)!=after.get(name)}
        root_audit.write(audit_path(prefix,phase,'manifest.json'),changes)
        state.update(finished_utc=datetime.now(timezone.utc).isoformat(),changed_paths=len(changes),
            evidence_sha256={suffix:digest(audit_path(prefix,phase,suffix)) for suffix in ('intent.json','before.json','after.json','manifest.json')})
        success=not failed and type(state['command_exit']) is int and state['command_exit']==0 and type(state['postcheck_exit']) is int and state['postcheck_exit']==0
        state['state']='complete' if success else 'failed'
        root_audit.write(audit_path(prefix,phase,'complete.json' if success else 'failed.json'),state)
        running.unlink()
        descriptor=os.open(running.parent,os.O_DIRECTORY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
    if not success:raise ValueError('voice_native_write_postconditions_incomplete')


def require_write_audit(prefix,phase,*,inputs=None,command=None,record_sha256=None):
    terminal=audit_path(prefix,phase,'complete.json');value=read(terminal)
    if (value.get('version')!=1 or value.get('state')!='complete' or value.get('phase')!=phase
            or type(value.get('command_exit')) is not int or value['command_exit']!=0
            or type(value.get('postcheck_exit')) is not int or value['postcheck_exit']!=0
            or value.get('pins')!=audit_pins() or audit_path(prefix,phase,'failed.json').exists()
            or (BUILD_LOCK.parent/(prefix.name+'.'+phase+'-audit.running.json')).exists()):raise ValueError('voice_native_write_audit_not_successful')
    if record_sha256 is not None and value.get('package_record_sha256')!=record_sha256:raise ValueError('voice_native_write_package_record_changed')
    if inputs is not None and value['inputs']!=inputs:raise ValueError('voice_native_write_inputs_changed')
    if command is not None and value['command']!=command:raise ValueError('voice_native_write_command_changed')
    for suffix,expected in value['evidence_sha256'].items():
        if suffix not in ('intent.json','before.json','after.json','manifest.json') or digest(audit_path(prefix,phase,suffix))!=expected:raise ValueError('voice_native_write_evidence_changed')
    if set(value['evidence_sha256'])!={'intent.json','before.json','after.json','manifest.json'}:raise ValueError('voice_native_write_evidence_missing')
    intent=read(audit_path(prefix,phase,'intent.json'))
    if any(value[key]!=intent[key] for key in ('phase','command','inputs','pins')):raise ValueError('voice_native_write_intent_changed')
    before=read(audit_path(prefix,phase,'before.json'));after=read(audit_path(prefix,phase,'after.json'))
    changes={name:{'before':before.get(name),'after':after.get(name)} for name in sorted(before.keys()|after.keys()) if before.get(name)!=after.get(name)}
    if read(audit_path(prefix,phase,'manifest.json'))!=changes or value['changed_paths']!=len(changes):raise ValueError('voice_native_write_manifest_changed')
    return digest(terminal)


def install_inputs(prefix,value):
    return {'prepared_sha256':digest(Path(str(prefix)+'.prepared.json')),
        'qualification_sha256':digest(Path(str(prefix)+'.qualified.json')),
        'source_archive_sha256':value['input']['sha256']}


def prepare(component,generation,cache):
    source,work,prefix=paths(component,generation)
    for path in (source,work,Path(str(prefix)+'.prepared.json'),Path(str(prefix)+'.preparing.json')):
        if os.path.lexists(path):raise ValueError('voice_generation_exists_inspect_do_not_replay')
    if cache!=T/'sources':raise ValueError('voice_native_cache_must_be_target_sources')
    lock=load_lock(R/'runtime/voice/native-inputs.lock.json');rows={r['id']:r for r in lock['artifacts']}
    kind,version,recipe,binary=COMPONENTS[component]
    needed=[kind]
    if component in ('whisper-cpp','toddy-voice-model-base'):needed+=['whisper-model-card','whisper-original-license']
    if component=='whisper-cpp':needed+=['whisper-base-model']
    for ident in needed:verify_file(cache/rows[ident]['filename'],rows[ident])
    reserve(384*1024**2);L.mkdir(parents=True,exist_ok=True)
    write_new(Path(str(prefix)+'.preparing.json'),{'component':component,'generation':generation,'state':'preparing-inspect-if-interrupted'})
    source.parent.mkdir(parents=True,exist_ok=True);work.parent.mkdir(parents=True,exist_ok=True)
    work.mkdir(mode=0o755);os.chown(work,101,101)
    correction=None
    if recipe:
        with tarfile.open(cache/rows[kind]['filename']) as bundle:
            members=bundle.getmembers();root,_=validate_members(kind,members)
            temporary=source.with_name(source.name+'-extracting');temporary.mkdir()
            bundle.extractall(temporary,filter='data')
        (temporary/root).rename(source);temporary.rmdir();correction=patch_source(kind,source)
        shutil.copyfile(R/'scripts/build/phase2'/recipe,source/'toddy-build.sh')
        qualification=source/'qualification';qualification.mkdir()
        shutil.copyfile(R/'scripts/build/phase2/voice_consumer.py',qualification/'consumer.py')
        if component=='whisper-cpp':
            process=qualification/'process-runtime';(process/'runtime/voice').mkdir(parents=True);(process/'tests').mkdir()
            for name in ('child.py','process.py','artifacts.py','session.py'):
                shutil.copyfile(R/'runtime/voice'/name,process/'runtime/voice'/name)
            shutil.copyfile(R/'tests/test_voice_process.py',process/'tests/test_voice_process.py')
            shutil.copyfile(R/'scripts/build/phase2/voice_process_qualify.py',qualification/'process-check.py')
            shutil.copytree(R/'tests/fixtures/voice/human',qualification/'human')
            shutil.copyfile(cache/rows['whisper-base-model']['filename'],qualification/'ggml-base.bin')
        recipe_sha=digest(source/'toddy-build.sh')
    else:
        source.mkdir();stage=work/'stage';model=stage/binary;model.parent.mkdir(parents=True)
        shutil.copyfile(cache/rows[kind]['filename'],model)
        doc=stage/'usr/share/doc/toddy-voice-model-base';doc.mkdir(parents=True)
        for ident in ('whisper-original-license','whisper-model-card'):
            shutil.copyfile(cache/rows[ident]['filename'],doc/rows[ident]['filename'])
        (doc/'copyright').write_bytes((cache/rows['whisper-original-license']['filename']).read_bytes()+b'\nConverted model card:\n'+(cache/rows['whisper-model-card']['filename']).read_bytes())
        (doc/'provenance.json').write_text(json.dumps({'model':rows[kind],'terms':lock['model_terms'],'notices':[rows[x] for x in ('whisper-original-license','whisper-model-card')]},indent=2)+'\n')
        (source/'model-input.json').write_text(json.dumps(rows[kind])+'\n');recipe_sha=None
        for path in stage.rglob('*'):path.chmod(0o755 if path.is_dir() else 0o644)
    # Cache acquisition uses0600; declared readonly input must be readable UID101.
    for path in source.rglob('*'):
        if not path.is_symlink():path.chmod(0o755 if path.is_dir() or path.stat().st_mode&0o111 else 0o644)
    source.chmod(0o755)
    value={'component':component,'generation':generation,'version':version,'input':rows[kind],'correction':correction,'recipe_sha256':recipe_sha,'driver_sha256':digest(Path(__file__)),'harness_sha256':digest(R/'scripts/build/phase2/isolated.sh'),'source_manifest_sha256':inspect_stage(source)['manifest_sha256'],'scope':'Prepared only; no native or audio acceptance'}
    write_new(Path(str(prefix)+'.prepared.json'),value)
    return value


def isolated_job(component,generation,phase):
    source,work,prefix,value=prepared(component,generation)
    marker=Path(str(prefix)+f'.{phase}.json')
    write_new(marker,{'state':'running-no-replay','prepared_sha256':digest(Path(str(prefix)+'.prepared.json'))})
    command=['bash',str(R/'scripts/build/phase2/isolated.sh'),str(source),str(work)]
    command+=['bash','/src/toddy-build.sh'] if phase=='build' else ['python3','/src/qualification/consumer.py',component,*(['installed'] if phase=='installed-consumer' else [])]
    if phase=='process':command=['bash',str(R/'scripts/build/phase2/isolated.sh'),str(source),str(work),'python3','/src/qualification/process-check.py']
    with Path(str(prefix)+f'.{phase}.log').open('xb') as stream:
        result=subprocess.run(command,stdout=stream,stderr=stream)
    write_new(Path(str(prefix)+f'.{phase}.exit.json'),{'exit':result.returncode,'command':command,'prepared_sha256':digest(Path(str(prefix)+'.prepared.json'))})
    if result.returncode:raise ValueError('voice_native_'+phase+'_failed_inspect_log')


def build(component,generation):
    if component=='toddy-voice-model-base':raise ValueError('model_is_data_no_build')
    isolated_job(component,generation,'build')


def elf_dependencies(binary):
    header=subprocess.check_output(['readelf','-h',str(binary)],text=True)
    if 'Advanced Micro Devices X86-64' not in header or not re.search(r'Type:\s+(?:EXEC|DYN)',header):raise ValueError('voice_native_elf_architecture')
    dynamic=subprocess.check_output(['readelf','-d',str(binary)],text=True)
    if '(RPATH)' in dynamic or '(RUNPATH)' in dynamic:raise ValueError('voice_native_embedded_search_path')
    needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic)
    providers={};seen=set();pending=list(needed)
    # Resolve each SONAME from the actual target's ldconfig, recursively. Do not
    # use host ldd or assume the builder's dependency versions are target versions.
    cache=subprocess.check_output(['chroot',str(T),'ldconfig','-p'],text=True)
    resolved={name:path for name,path in re.findall(r'^\s*(\S+)\s+\([^\n]+\) => (\S+)$',cache,re.M)}
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        if name not in resolved:raise ValueError('voice_elf_dependency_missing_'+name)
        path=resolved[name];real=(T/path.lstrip('/')).resolve(strict=True)
        if not real.is_relative_to(T):raise ValueError('voice_dependency_escape')
        ownership=subprocess.check_output(['chroot',str(T),'dpkg-query','-S','/'+str(real.relative_to(T))],text=True)
        owners={line.split(': ',1)[0] for line in ownership.strip().splitlines()}
        if len(owners)!=1:raise ValueError('voice_dependency_ownership')
        owner=owners.pop()
        version=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',owner],text=True)
        providers[owner]=version
        text=subprocess.check_output(['readelf','-d',str(real)],text=True)
        pending+=re.findall(r'\(NEEDED\).*?\[(.*?)\]',text)
    return {'needed':needed,'providers':providers}


def qualify(component,generation):
    source,work,prefix,value=prepared(component,generation)
    proof=Path(str(prefix)+'.qualified.json')
    if proof.exists():raise ValueError('voice_qualification_exists')
    if component!='toddy-voice-model-base':
        result=read(Path(str(prefix)+'.build.exit.json'))
        if result['exit']!=0 or result['prepared_sha256']!=digest(Path(str(prefix)+'.prepared.json')):raise ValueError('voice_build_not_successful')
        tests=read(work/'test-results.json');budget=read(work/'build-budget.json')
        if not 1<=budget.get('jobs',0)<=8:raise ValueError('voice_build_budget_missing')
        if component=='espeak-ng' and tests.get('upstream_ctest_exit')!=0:raise ValueError('voice_original_tests_failed')
        dependencies={'needed':[],'providers':{}}
        for binary in sorted((work/'stage').rglob('*')):
            if binary.is_file() and not binary.is_symlink():
                with binary.open('rb') as stream:magic=stream.read(4)
                if magic==b'\x7fELF':
                    closure=elf_dependencies(binary);dependencies['needed']+=closure['needed'];dependencies['providers'].update(closure['providers'])
        if not dependencies['needed']:raise ValueError('voice_native_elf_missing')
        isolated_job(component,generation,'consumer')
        consumer=read(work/'consumer.json')
        if set(consumer['samples'])!={'en','pt-BR'}:raise ValueError('voice_bilingual_consumer_missing')
    else:
        dependencies={'providers':{},'needed':[]};consumer={'scope':'Verified immutable model bytes and exact original MIT license/card; no independent inference in data package'}
        model=work/'stage'/COMPONENTS[component][3]
        verify_file(model,value['input'])
    legal={}
    if component=='toddy-voice-model-base':
        rows={r['id']:r for r in load_lock(R/'runtime/voice/native-inputs.lock.json')['artifacts']}
        for ident in ('whisper-original-license','whisper-model-card'):
            document=work/'stage/usr/share/doc/toddy-voice-model-base'/rows[ident]['filename']
            verify_file(document,rows[ident]);legal[ident]=digest(document)
    else:
        documents=[('COPYING','COPYING')] if component=='espeak-ng' else [('LICENSE','LICENSE'),('ggml/LICENSE','GGML-LICENSE')]
        for original,name in documents:
            document=work/'stage/usr/share/doc'/component/name
            if document.is_symlink() or digest(document)!=digest(source/original):raise ValueError('voice_stage_notice_changed')
            legal[name]=digest(document)
    inspection=inspect_stage(work/'stage')
    result={'component':component,'version':value['version'],'prepared_sha256':digest(Path(str(prefix)+'.prepared.json')),'stage_manifest_sha256':inspection['manifest_sha256'],'dependencies':dependencies,'legal_documents':legal,'consumer':consumer,'scope':'Native engine/file-only or model data qualification; no microphone/playback/GNOME acceptance'}
    write_new(proof,result);return result


def verify_package_record(record,target):
    if record.get('installed') is not True:raise ValueError('voice_native_record_not_installed')
    if not record.get('payload'):raise ValueError('voice_empty_package_record')
    for name,row in record['payload'].items():
        if not name.startswith('/') or '..' in Path(name).parts or any(ord(c)<32 for c in name):raise ValueError('voice_package_record_path')
        path=target/name.lstrip('/')
        if not path.parent.resolve().is_relative_to(target.resolve()):raise ValueError('voice_package_record_escape')
        info=path.lstat()
        if (info.st_mode,info.st_uid,info.st_gid)!=(row['mode'],0,0):raise ValueError('voice_installed_ownership')
        if 'sha256' in row and (path.is_symlink() or digest(path)!=row['sha256']):raise ValueError('voice_installed_payload_hash')
        if 'symlink' in row and os.readlink(path)!=row['symlink']:raise ValueError('voice_installed_payload_link')


def install(component,generation,*,lease=None):
    source,work,prefix,value=prepared(component,generation);q=read(Path(str(prefix)+'.qualified.json'))
    if q['prepared_sha256']!=digest(Path(str(prefix)+'.prepared.json')) or q['stage_manifest_sha256']!=inspect_stage(work/'stage')['manifest_sha256']:raise ValueError('voice_qualified_stage_changed')
    version=COMPONENTS[component][1];architecture='all' if component=='toddy-voice-model-base' else 'amd64'
    dest=T/'sources/stage'/prefix.name;ledger=Path(str(prefix)+'.install.json')
    if dest.exists() or ledger.exists():raise ValueError('voice_install_uncertain_inspect_do_not_replay')
    existing=subprocess.run(['chroot',str(T),'dpkg-query','-W',component],capture_output=True)
    if existing.returncode!=1:raise ValueError('voice_existing_package_requires_reviewed_update')
    reserve(384*1024**2)
    dependencies=', '.join(name+' (= '+version+')' for name,version in sorted(q['dependencies']['providers'].items()))
    command=[sys.executable,str(R/'scripts/build/stage_package.py'),component,version,str(dest),'--architecture',architecture,'--source',value['input']['filename'],'--recipe','scripts/build/phase2/voice-install.sh',*(['--depends',dependencies] if dependencies else []),'--install']
    with native_write_audit(prefix,'install',command,install_inputs(prefix,value),lease) as audit:
        write_new(ledger,{'state':'install-intended-no-replay','qualification_sha256':digest(Path(str(prefix)+'.qualified.json'))})
        shutil.copytree(work/'stage',dest,symlinks=True)
        if component!='toddy-voice-model-base':
            from package_copyright import write_copyright
            write_copyright(dest,component,[value['input']['filename']])
            names=['COPYING','COPYING.APACHE','COPYING.BSD2','COPYING.UCD','README.md'] if component=='espeak-ng' else ['LICENSE','ggml/LICENSE']
            notice=b'Exact upstream license overview for local speech review. Per-file attribution and conditions remain in source-notices/index.json and the source archive.\n'
            for name in names:
                notice+=('\nSource document: '+name+'\n').encode()+(source/name).read_bytes()+b'\n'
            if len(notice)>65536:raise ValueError('voice_legal_overview_too_large')
            (dest/'usr/share/doc'/component/'VOICE-LICENSES.txt').write_bytes(notice)
        result=subprocess.run(command,cwd=R,check=True)
        audit['command_exit']=result.returncode
        record=Path('/var/log/toddy/packages')/f'{component}_{version}_{architecture}.json'
        verify_package_record(read(record),T)
        audit['postcheck_exit']=0
        audit['package_record_sha256']=digest(record)
    write_new(Path(str(prefix)+'.installed.json'),{'record_sha256':digest(record),'archive_sha256':read(record)['archive_sha256'],'native_write_audit_sha256':require_write_audit(prefix,'install',inputs=install_inputs(prefix,value)),'scope':'Native transaction and installed payload verified; final independent check still required'})


def check(component,generation):
    _,_,prefix,value=prepared(component,generation);architecture='all' if component=='toddy-voice-model-base' else 'amd64'
    record=Path('/var/log/toddy/packages')/f'{component}_{value["version"]}_{architecture}.json'
    installed=read(Path(str(prefix)+'.installed.json'))
    if installed.get('native_write_audit_sha256')!=require_write_audit(prefix,'install',inputs=install_inputs(prefix,value),record_sha256=installed['record_sha256']):raise ValueError('voice_install_write_audit_required')
    if digest(record)!=installed['record_sha256']:raise ValueError('voice_package_record_changed')
    verify_package_record(read(record),T)
    actual_path,_=native_record(component)
    if actual_path!=record:raise ValueError('voice_installed_version_changed')
    if subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip():raise ValueError('voice_dpkg_audit')
    subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
    if component!='toddy-voice-model-base':
        isolated_job(component,generation,'installed-consumer')
        verify_package_record(read(record),T)
    write_new(Path(str(prefix)+'.checked.json'),{'record_sha256':digest(record),'archive_sha256':read(record)['archive_sha256'],'qualification_sha256':digest(Path(str(prefix)+'.qualified.json')),'native_write_audit_sha256':installed['native_write_audit_sha256'],'scope':'Independent exact installed payload plus native dpkg/APT consistency; no device claim'})


def process(component,generation):
    if component!='whisper-cpp':raise ValueError('process_qualification_uses_whisper_generation')
    for name in COMPONENTS:
        _,_,other,prepared_value=prepared(name,generation)
        require_write_audit(other,'install',inputs=install_inputs(other,prepared_value))
        checked=read(Path(str(other)+'.checked.json'));path,_=native_record(name)
        if digest(path)!=checked['record_sha256'] or checked.get('native_write_audit_sha256')!=require_write_audit(other,'install',inputs=install_inputs(other,prepared_value),record_sha256=digest(path)):raise ValueError('voice_process_needs_installed_checked_engines_model')
    isolated_job(component,generation,'process')


def native_record(component):
    version=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',component],text=True)
    arch=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Architecture}',component],text=True)
    path=Path('/var/log/toddy/packages')/f'{component}_{version}_{arch}.json'
    regular(path);value=read(path);verify_package_record(value,T)
    archive=Path('/var/cache/toddy/packages')/f'{component}_{version}_{arch}.deb'
    regular(archive)
    if digest(archive)!=value['archive_sha256']:raise ValueError('voice_native_archive_changed')
    return path,value


def artifact(role,path,version,url,license_id,notice):
    target=T/path.lstrip('/');legal=T/notice.lstrip('/')
    info=regular(target);legal_info=regular(legal)
    if not 0<legal_info.st_size<=65536:raise ValueError('voice_notice_requires_bounded_exact_native_document')
    if role!='stt-model' and not info.st_mode&0o111:raise ValueError('voice_artifact_executable')
    return {'artifact_id':'native-'+role,'kind':'stt-model' if role=='stt-model' else 'engine','path':path,'size':info.st_size,'sha256':digest(target),'source_url':url,'version':version,'license_id':license_id,'license_path':notice,'license_sha256':digest(legal),'review':'reviewed-local-use','languages':['en','pt-BR']}


def catalog(component,generation,*,lease=None):
    if component!='whisper-cpp':raise ValueError('catalog_uses_whisper_generation')
    _,work,prefix,_=prepared(component,generation)
    exit=read(Path(str(prefix)+'.process.exit.json'));process_receipt=read(work/'process-qualified.json')
    if exit['exit']!=0 or exit['prepared_sha256']!=digest(Path(str(prefix)+'.prepared.json')) or process_receipt['tests_run']<3 or any(process_receipt[k]!=0 for k in ('failures','errors','skipped')):raise ValueError('voice_native_process_unqualified')
    for name,sha in process_receipt['files'].items():
        path=T/'usr/lib/toddy/voice'/name;regular(path)
        if digest(path)!=sha:raise ValueError('voice_installed_process_not_qualified')
    records={}
    for name in COMPONENTS:
        _,_,other,prepared_value=prepared(name,generation);require_write_audit(other,'install',inputs=install_inputs(other,prepared_value));check=read(Path(str(other)+'.checked.json'))
        path,value=native_record(name)
        if digest(path)!=check['record_sha256'] or check.get('native_write_audit_sha256')!=require_write_audit(other,'install',inputs=install_inputs(other,prepared_value),record_sha256=digest(path)):raise ValueError('voice_final_check_record_changed')
        records[name]=(path,value)
    versions={'pipewire':'1.6.8','wireplumber':'0.5.15','whisper-cpp':'1.9.5','espeak-ng':'1.52.0'}
    for name in ('pipewire','wireplumber','toddy-voice'):records[name]=native_record(name)
    for name,version in versions.items():
        if records[name][1]['version'].split('-1+toddy',1)[0]!=version:raise ValueError('voice_frozen_native_dependency_changed')
    specs=[('capture','/usr/lib/toddy/voice/pw-record','0.2.0','https://github.com/markaraujo/toddy-os','MIT','/usr/share/doc/toddy-voice/copyright'),
     ('playback','/usr/lib/toddy/voice/pw-play','0.2.0','https://github.com/markaraujo/toddy-os','MIT','/usr/share/doc/toddy-voice/copyright'),
     ('device-list','/usr/bin/pw-dump','1.6.8',records['pipewire'][1]['sources'][0]['url'],'MIT','/usr/share/doc/pipewire/copyright'),
     ('stt-engine','/usr/bin/whisper-cli','1.9.5',records['whisper-cpp'][1]['sources'][0]['url'],'MIT','/usr/share/doc/whisper-cpp/VOICE-LICENSES.txt'),
     ('stt-model','/usr/share/toddy/voice/models/ggml-base.bin',COMPONENTS['toddy-voice-model-base'][1].split('-1+toddy',1)[0],records['toddy-voice-model-base'][1]['sources'][0]['url'],'MIT','/usr/share/doc/toddy-voice-model-base/whisper-original-license.txt'),
     ('tts-engine','/usr/bin/espeak-ng','1.52.0',records['espeak-ng'][1]['sources'][0]['url'],'LicenseRef-eSpeak-NG-per-file','/usr/share/doc/espeak-ng/VOICE-LICENSES.txt')]
    artifacts={spec[0]:artifact(*spec) for spec in specs}
    # Match every root wrapper with the reviewed source bytes before enabling;
    # pw-record/pw-play distro symlinks are never promoted as approved wrappers.
    for role in ('capture','playback'):
        expected=R/'runtime/voice/wrappers'/('pw-record' if role=='capture' else 'pw-play')
        if artifacts[role]['sha256']!=digest(expected):raise ValueError('voice_wrapper_not_reviewed_source')
    if set(process_receipt.get('file_sessions',{}))!={'en','pt-BR'} or process_receipt.get('native_engine_stop',{}).get('code')!='canceled':raise ValueError('voice_actual_session_unqualified')
    for role in ('capture','playback','device-list'):
        if process_receipt['transport'][role]['sha256']!=artifacts[role]['sha256']:raise ValueError('voice_transport_not_qualified')
    transport=T/'usr/bin/pw-cat';info=regular(transport)
    if process_receipt['transport']['pw-cat']['sha256']!=digest(transport):raise ValueError('voice_native_transport_changed')
    value={'voice_catalog_version':1,'status':'native-qualified','tts_engine':'espeak-ng','native_dependencies':{name:{'version':version,'component_record_sha256':digest(records[name][0])} for name,version in versions.items()},'process_control':{'launcher_sha256':process_receipt['files']['child.py'],'runner_sha256':process_receipt['files']['process.py'],'pw_cat_sha256':digest(transport),'pw_cat_bytes':info.st_size,'evidence_sha256':digest(work/'process-qualified.json')},'artifacts':artifacts}
    receipt=Path(str(prefix)+'.catalog.json');destination=T/'usr/share/toddy/voice/catalog.json'
    if destination.exists() or receipt.exists():raise ValueError('voice_catalog_exists_explicit_update_required')
    code="import sys;sys.path.insert(0,'/usr/lib');from toddy.voice.catalog import NativeVoiceCatalog;value=NativeVoiceCatalog().preview();assert value['languages']==['en','pt-BR'];assert value['always_listening'] is False;assert value['automatic_download'] is False"
    command=['chroot','--userspec=101:101','--groups=101',str(T),'/usr/bin/env','-i','HOME=/tmp','PATH=/usr/bin:/usr/sbin','LC_ALL=C','/usr/bin/python3','-I','-c',code]
    inputs={'process_evidence_sha256':digest(work/'process-qualified.json'),'catalog_value_sha256':hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()}
    with native_write_audit(prefix,'catalog',command,inputs,lease) as audit:
        destination.parent.mkdir(parents=True,exist_ok=True)
        write_new(destination,value);destination.chmod(0o644)
        result=subprocess.run(command,check=True,timeout=30)
        audit['command_exit']=result.returncode
        audit['postcheck_exit']=0
    write_new(receipt,{'catalog_sha256':digest(destination),'native_write_audit_sha256':require_write_audit(prefix,'catalog',inputs=inputs,command=command),'generated_path':'/usr/share/toddy/voice/catalog.json','records':{name:digest(path) for name,(path,_) in records.items()},'process_evidence_sha256':digest(work/'process-qualified.json'),'scope':'Explicit native artifact/license/process gate only; owner still reviews notices/devices. Actual PTT/playback/GNOME evidence remains separate.'})
    return value


def catalog_package(component,generation,*,lease=None):
    if component!='whisper-cpp':raise ValueError('catalog_package_uses_whisper_generation')
    _,_,prefix,_=prepared(component,generation)
    receipt=Path(str(prefix)+'.catalog.json');value=read(receipt)
    if value.get('native_write_audit_sha256')!=require_write_audit(prefix,'catalog'):raise ValueError('voice_catalog_write_audit_required')
    source=T/'usr/share/toddy/voice/catalog.json';regular(source)
    if digest(source)!=value['catalog_sha256']:raise ValueError('voice_qualified_catalog_changed')
    name='toddy-voice-native-catalog';version='0.2.0-1+toddy1'
    dest=T/'sources/stage'/f'{name}-{generation}'
    marker=Path(str(prefix)+'.catalog-package.json')
    if dest.exists() or marker.exists():raise ValueError('voice_catalog_package_uncertain_no_replay')
    depends=[]
    for package,sha in value['records'].items():
        path,record=native_record(package)
        if digest(path)!=sha:raise ValueError('voice_catalog_record_changed')
        depends.append(package+' (= '+record['version']+')')
    reserve(16*1024**2)
    command=[sys.executable,str(R/'scripts/build/stage_package.py'),name,version,str(dest),'--architecture','all','--recipe','scripts/build/phase2/voice-install.sh','--depends',', '.join(sorted(depends)),'--install']
    inputs={'catalog_receipt_sha256':digest(receipt),'catalog_sha256':value['catalog_sha256']}
    with native_write_audit(prefix,'catalog-package',command,inputs,lease) as audit:
        write_new(marker,{'state':'install-intended-no-replay','catalog_receipt_sha256':digest(receipt)})
        target=dest/'usr/share/toddy/voice/catalog.json';target.parent.mkdir(parents=True)
        shutil.copyfile(source,target)
        doc=dest/'usr/share/doc'/name;doc.mkdir(parents=True)
        shutil.copyfile(receipt,doc/'qualification.json')
        _,work,_,_=prepared(component,generation)
        shutil.copyfile(work/'process-qualified.json',doc/'process-qualified.json')
        for engine in COMPONENTS:
            _,_,other,_=prepared(engine,generation)
            shutil.copyfile(Path(str(other)+'.qualified.json'),doc/(engine+'-qualified.json'))
        shutil.copyfile(R/'tests/fixtures/voice/human/manifest.json',doc/'human-sample-attribution.json')
        shutil.copyfile(R/'tests/fixtures/voice/human/README.md',doc/'human-samples.md')
        shutil.copyfile(R/'LICENSE',doc/'MIT')
        shutil.copyfile(R/'LICENSES/CC-BY-4.0.txt',doc/'CC-BY-4.0')
        (doc/'copyright').write_bytes((R/'LICENSE').read_bytes()+b'\nQualification documentation:\n'+(R/'LICENSES/CC-BY-4.0.txt').read_bytes())
        result=subprocess.run(command,cwd=R,check=True)
        audit['command_exit']=result.returncode
        path,record=native_record(name)
        audit['postcheck_exit']=0
        audit['package_record_sha256']=digest(path)
    write_new(Path(str(prefix)+'.catalog-package-installed.json'),{'record_sha256':digest(path),'archive_sha256':record['archive_sha256'],'native_write_audit_sha256':require_write_audit(prefix,'catalog-package',inputs=inputs,command=command),'scope':'Owned optional native artifact/catalog package only; no automatic model consent or audio activation'})


def extras(component,generation):
    if component!='whisper-cpp':raise ValueError('extras_uses_whisper_generation')
    _,_,prefix,_=prepared(component,generation)
    installed=read(Path(str(prefix)+'.catalog-package-installed.json'));catalog_path,_=native_record('toddy-voice-native-catalog')
    if digest(catalog_path)!=installed['record_sha256']:raise ValueError('voice_catalog_package_changed')
    if installed.get('native_write_audit_sha256')!=require_write_audit(prefix,'catalog-package',record_sha256=installed['record_sha256']):raise ValueError('voice_catalog_package_write_audit_required')
    packages=[]
    for name in (*COMPONENTS,'toddy-voice','toddy-voice-native-catalog'):
        path,record=native_record(name)
        archive=Path('/var/cache/toddy/packages')/(path.stem+'.deb')
        packages.append({'name':name,'version':record['version'],'archive':archive.name,'archive_sha256':record['archive_sha256'],'archive_bytes':archive.stat().st_size,'component_record_sha256':digest(path),'sources':record['sources'],'depends':subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Depends}',name],text=True),'payload_regular_bytes':sum(row.get('size',row.get('bytes',0)) for row in record['payload'].values()),'license_path':'/usr/share/doc/'+name+'/copyright'})
    output={'voice_extras_version':1,'status':'native-qualified-awaiting-signed-release','available':False,'offline_base':False,'iso_inclusion':False,'automatic_download':False,'automatic_activation':False,'owner_network_license_review_required':True,'signed_project_repository':None,'packages':packages,'scope':'Publication input only. Release signer must bind actual project repository identity, signed APT metadata and exact dependency closure before presenting availability; never convert this unsigned builder receipt to owner authorization.'}
    write_new(Path(str(prefix)+'.extras.json'),output);return output


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','build','qualify','install','check','process','catalog','catalog-package','extras']);p.add_argument('component',choices=COMPONENTS);p.add_argument('generation');a=p.parse_args()
    if os.getuid()!=0 or Path(__file__).resolve()!=R/'scripts/build/phase2/voice_native.py':raise SystemExit('Dedicated native builder only')
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    os.umask(0o022)
    os.environ['LC_ALL']='C'
    # Harness owns the same global lock during its child. Holding it here too
    # would deadlock; all other root phases retain it throughout their operation.
    pipeline=Path('/var/log/toddy/build/voice-pipeline.lock').open('a')
    fcntl.flock(pipeline,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if a.phase in ('build','qualify','check','process'):
        result=globals()[a.phase.replace('-','_')](a.component,a.generation)
    else:
        with BUILD_LOCK.open('a') as lease:
            fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if list(Path('/var/log/toddy/build').glob('*.running.json')):raise ValueError('voice_unreconciled_native_job')
            result=prepare(a.component,a.generation,T/'sources') if a.phase=='prepare' else globals()[a.phase.replace('-','_')](a.component,a.generation,**({'lease':lease} if a.phase in ('install','catalog','catalog-package') else {}))
    if result:print(json.dumps(result,indent=2))

if __name__=='__main__':main()
