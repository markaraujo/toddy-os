"""Build only same-version PAM-related Systemd runtime and affected unit drivers."""
import hashlib,json,os,pickle,re,shutil,subprocess,sys
from pathlib import Path
assert os.getuid()==101
stage_only=sys.argv[1:]==['--stage-only'];assert stage_only or len(sys.argv)==1
source=Path('/src');work=Path('/build');compile_dir=work/'compile'
assert (source/'src/core/load-fragment-gperf.gperf.in').is_file()
assert compile_dir.exists() if stage_only else not compile_dir.exists()
old=(source/'build/config.h').read_text();old_options=json.loads((source/'build/meson-info/intro-buildoptions.json').read_text())
def macros(text):return dict(re.findall(r'^#define ((?:HAVE|ENABLE)_[A-Z0-9_]+) ([01])$',text,re.M))
baseline=macros(old);assert baseline['HAVE_PAM']=='0'
args=['meson','setup',str(compile_dir),str(source),'--prefix=/usr','--libdir=lib','--buildtype=release','--wrap-mode=nofallback','-Ddefault-dnssec=no','-Dfirstboot=false','-Dinstall-tests=false','-Dldconfig=false','-Dsysusers=false','-Drpmmacrosdir=no','-Dhomed=disabled','-Dman=disabled','-Dhtml=disabled','-Dmode=release','-Dpam=enabled','-Dpamconfdir=/etc/pam.d','-Dpamlibdir=/usr/lib/security','-Ddev-kvm-mode=0660','-Dnobody-group=nogroup','-Dsysupdate=disabled','-Dukify=disabled','-Ddocdir=/usr/share/doc/systemd-261.2']
# Prevent new desktop development libraries from silently changing accepted
# optional runtime features. PAM is the only intentional feature delta.
for option in old_options:
    name=option['name'];macro='HAVE_'+name.upper().replace('-','_')
    if option['section']=='user' and option.get('value')=='auto' and option.get('choices')==['enabled','disabled','auto'] and baseline.get(macro)=='0' and name!='pam':args.append('-D'+name+'=disabled')
for name,macro in [('bootloader','ENABLE_BOOTLOADER'),('bpf-framework','HAVE_LIBBPF')]:
    if baseline.get(macro)=='0':args.append('-D'+name+'=disabled')
if stage_only:assert json.loads((work/'setup-command.json').read_text())==args
else:
    (work/'setup-command.json').write_text(json.dumps(args,indent=2)+'\n')
    subprocess.run(args,check=True)
current=macros((compile_dir/'config.h').read_text());delta={k:{'old':baseline.get(k),'new':current.get(k)} for k in sorted(baseline.keys()|current.keys()) if baseline.get(k)!=current.get(k)}
(work/'feature-delta.json').write_text(json.dumps(delta,indent=2)+'\n')
assert delta=={'HAVE_PAM':{'old':'0','new':'1'}},'Review concrete feature delta before compilation; never silently broaden profile'
rows=json.loads((compile_dir/'meson-info/intro-targets.json').read_text())
wanted={('systemd','executable'),('systemd-executor','executable'),('systemd-core-261','shared library'),('systemd-shared-261','shared library'),('pam_systemd','shared library'),('systemd-user','custom')}
tests=['test-load-fragment','test-unit-serialize','test-login-tables','test-login-util','test-login-shared','test-serialize']
selected=[r for r in rows if (r['name'],r['type']) in wanted or (r['name'] in tests and r['type']=='executable')]
assert len(selected)==len(wanted)+len(tests),[(r['name'],r['type']) for r in selected]
targets=[str(Path(n).relative_to(compile_dir)) for row in selected for n in row['filename']]
if not stage_only:
    subprocess.run(['ninja','-C',str(compile_dir),'-j4',*targets],check=True)
    with (work/'affected-original-tests.log').open('x') as log:
        result=subprocess.run(['meson','test','-C',str(compile_dir),'--no-rebuild','--print-errorlogs','-j2',*tests],stdout=log,stderr=subprocess.STDOUT)
    (work/'affected-original-tests.exit').write_text(str(result.returncode)+'\n')
assert (work/'affected-original-tests.exit').read_text().strip()=='0'
results=[json.loads(s) for s in (compile_dir/'meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert {r['name'].split(':')[-1] for r in results}==set(tests) and len(results)==6
for r in results:
    if r['result']=='SKIP':
        assert r['returncode']==77 and r['name'].split(':')[-1] in ['test-load-fragment','test-unit-serialize']
        assert 'cgroupfs v2 is not mounted.' in r['stderr'] and 'cgroupfs not available, skipping tests.' in r['stderr']
    else:assert r['result']=='OK' and r['returncode']==0
before={str(Path(n).relative_to(compile_dir)):hashlib.sha256(Path(n).read_bytes()).hexdigest() for r in selected for n in r['filename']}

# Copy only the declared runtime delta. No full Systemd installation or daemon
# reload is performed by the unprivileged compiler.
paths={'systemd':'usr/lib/systemd/systemd','systemd-executor':'usr/lib/systemd/systemd-executor','systemd-core-261':'usr/lib/systemd/libsystemd-core-261.so','systemd-shared-261':'usr/lib/systemd/libsystemd-shared-261.so','pam_systemd':'usr/lib/security/pam_systemd.so','systemd-user':'etc/pam.d/systemd-user'}
stage=Path('/stage');assert not list(stage.iterdir()) and not (work/'stage-results.json').exists()
artifacts={};transitions=[]
from mesonbuild.scripts.depfixer import fix_elf
install=pickle.load((compile_dir/'meson-private/install.dat').open('rb'))
install_targets={str(Path(row.fname)):row for row in install.targets}

for row in selected:
    if row['name'] not in paths:continue
    original,=row['filename'];dst=stage/paths[row['name']];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,dst)
    compiled_sha=hashlib.sha256(dst.read_bytes()).hexdigest()
    if dst.read_bytes()[:4]==b'\x7fELF':
        planned=install_targets[str(Path(original).relative_to(compile_dir))]
        assert Path(planned.outdir)/dst.name==Path('/')/paths[row['name']]
        fix_elf(str(dst),planned.rpath_dirs_to_remove,planned.install_rpath.encode(),False)
        dynamic=subprocess.check_output(['readelf','-d',str(dst)],text=True)
        assert '/build/' not in dynamic and '/src/' not in dynamic
        transitions.append({'path':paths[row['name']],'compiled_sha256':compiled_sha,'staged_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'meson_install_rpath':planned.install_rpath})
    artifacts[paths[row['name']]]=hashlib.sha256(dst.read_bytes()).hexdigest()
assert len(artifacts)==6
assert before=={str(Path(n).relative_to(compile_dir)):hashlib.sha256(Path(n).read_bytes()).hexdigest() for r in selected for n in r['filename']}
env=dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib/systemd')
version=subprocess.run(['/stage/usr/lib/systemd/systemd','--version'],text=True,capture_output=True,env=env,check=True)
assert version.stdout.splitlines()[0]=='systemd 261 (261.2)' and '+PAM' in version.stdout.splitlines()[1]
import ctypes
module=ctypes.CDLL('/stage/usr/lib/security/pam_systemd.so');assert module.pam_sm_open_session and module.pam_sm_close_session

(work/'stage-results.json').write_text(json.dumps({'scope':'Only same-version Systemd PAM runtime delta, staged loader/CLI and six affected original drivers (retain two exact cgroup prerequisite skips); native two-driver/boot/session gate remains mandatory','compile_exit':0,'stage_exit':0,'staged_version_exit':0,'staged_module_load_exit':0,'unchanged_selected_artifacts':before,'feature_delta':delta,'artifacts':artifacts,'meson_rpath_transitions':transitions,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in results],'unqualified':'New PID1/core/executor and pam_systemd require controlled native boot, PAMName allow/deny, logind/user-session/recovery validation before acceptance'},indent=2)+'\n')
