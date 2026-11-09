#!/usr/bin/env python3
"""Prepare a selected immutable source/recipe input, never install it."""
import hashlib
import json
from pathlib import Path
import shlex
import re
import subprocess
import sys
import phase2_vm
ROOT=phase2_vm.ROOT
NAME=sys.argv[1]
assert len(sys.argv) in (2,3)
receipt_suffix='-'+sys.argv[2] if len(sys.argv)==3 else ''
assert not receipt_suffix or re.fullmatch(r'-[a-z][a-z0-9-]{0,31}',receipt_suffix)
assert NAME in ('wayland','wayland-protocols','pixman','libpng','freetype','fontconfig','fribidi','harfbuzz','cairo','pango','graphene','shared-mime-info','llvm','adwaita-fonts','dejavu-fonts','libjpeg-turbo','psutil','mako','libpciaccess','libdrm','pyyaml','mesa','libepoxy','gdk-pixbuf','tiff','iso-codes','gtk','doxygen','itstool','libxmlb','libfyaml','appstream','libadwaita','libsass','sassc','at-spi2-core','lcms2','libseccomp','bubblewrap','hwdata','libdisplay-info','mtdev','libevdev','libxcvt','libei','libinput')
if __name__=='__main__':
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==NAME)
    archive=ROOT/'.local/sources'/row['filename'];data=archive.read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    probes={'libinput':'libinput-probe.c','libei':'libei-probe.c','libxcvt':'libxcvt-probe.c','libevdev':'libevdev-probe.c','mtdev':'mtdev-probe.c','libdisplay-info':'libdisplay-info-probe.c','bubblewrap':'bubblewrap-probe.py','libseccomp':'libseccomp-probe.c','lcms2':'lcms2-probe.c','at-spi2-core':'at-spi2-core-probe.c','sassc':'sassc-probe.py','libsass':'libsass-probe.c','libadwaita':'libadwaita-probe.c','appstream':'appstream-probe.c','libfyaml':'libfyaml-probe.c','libxmlb':'libxmlb-probe.c','itstool':'itstool-probe.py','doxygen':'doxygen-probe.py','iso-codes':'iso-codes-probe.py','gtk':'gtk-probe.c','tiff':'tiff-probe.c','gdk-pixbuf':'gdk-pixbuf-probe.c','libepoxy':'libepoxy-probe.c','mesa':'mesa-probe.c','pyyaml':'pyyaml-probe.py','libpciaccess':'libpciaccess-probe.c','libdrm':'libdrm-probe.c','freetype':'freetype-probe.c','psutil':'psutil-probe.py','mako':'mako-probe.py'}
    probe_filename='toddy-probe.py' if probes.get(NAME,'').endswith('.py') else 'toddy-probe.c'
    probe=(ROOT/'scripts/build/phase2'/probes[NAME]).read_text() if NAME in probes else None
    private_bus=(ROOT/'scripts/build/phase2/atspi_private_bus.py').read_text() if NAME=='at-spi2-core' else None
    extra=None
    if NAME in ('shared-mime-info','llvm','libfyaml','libei'):
        extra_name='munit-test-dependency' if NAME=='libei' else 'check' if NAME=='libfyaml' else 'xdgmime-tests' if NAME=='shared-mime-info' else 'llvm-upstream-fix'
        extra=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==extra_name)
        extra_data=(ROOT/'.local/sources'/extra['filename']).read_bytes()
        assert hashlib.sha256(extra_data).hexdigest()==extra['sha256']
        transfer='''from pathlib import Path
import fcntl,hashlib,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={extra!r}\n'+'''
p=Path('/mnt/lfs/sources')/row['filename'];part=p.with_name(p.name+'.part')
assert not part.exists(),'Reconcile partial test-source transfer'
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==row['sha256']
if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
else:
 with part.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 part.rename(p)
'''
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(transfer)],input=extra_data,check=True)
    recipe=(ROOT/'scripts/build/phase2'/(NAME+'-build.sh')).read_text()
    remote='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\nrecipe={recipe!r}\nprobe={probe!r}\nprobe_filename={probe_filename!r}\nprivate_bus={private_bus!r}\nextra={extra!r}\n'+'''
base=Path('/mnt/lfs/sources');archive=base/row['filename'];part=base/(row['filename']+'.part')
source_name='AppStream-'+row['version'] if row['name']=='appstream' else 'iso-codes-v'+row['version'] if row['name']=='iso-codes' else 'llvm-project-'+row['version']+'.src' if row['name']=='llvm' else 'dejavu-fonts-ttf-'+row['version'] if row['name']=='dejavu-fonts' else row['name']+'-'+row['version']
source=base/'phase2/inputs'/source_name;work=base/'phase2/work'/(row['name']+'-1')
assert not source.exists() and not work.exists() and not part.exists(),'Reconcile existing source/job; no replay'
installed=subprocess.run(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status}',row['name']],capture_output=True,text=True)
assert installed.returncode in (0,1),'Cannot establish native package state'
assert installed.stdout.strip()!='install ok installed','Reuse installed owned package; generic preparation must not rebuild accepted foundation/runtime'
if archive.exists():
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['sha256']
    assert hashlib.sha256(sys.stdin.buffer.read()).hexdigest()==row['sha256']
else:
    digest=hashlib.sha256()
    with part.open('xb') as output:
        while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk);digest.update(chunk)
        output.flush();os.fsync(output.fileno())
    assert digest.hexdigest()==row['sha256'];part.rename(archive)
assert os.statvfs(base).f_bavail*os.statvfs(base).f_frsize>=16*1024**3
subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=base/'phase2/inputs',check=True)
patches=[]
if row['name']=='mako':
    import stat
    path=source/'doc/build/changelog.rst';before=stat.S_IMODE(path.stat().st_mode)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    assert before==0o600 and sha=='a5620499d6c083972b0ba7ea307b99b06e783966fa46b3e5c73d00fe96f51e31'
    path.chmod(0o644)
    patches.append({'path':'doc/build/changelog.rst','before_mode':before,'after_mode':0o644,
                    'content_sha256':sha,'reason':'Public release doc is owner-readable only; expose unchanged bytes to unprivileged read-only-input compiler'})
if row['name']=='libfyaml':
    assert extra['name']=='check'
    (source/'subprojects').mkdir(exist_ok=True)
    subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',extra['filename']],cwd=source/'subprojects',check=True)
if row['name']=='libei':
    assert extra['name']=='munit-test-dependency' and len(extra['commit'])==40
    folder=source/'subprojects';assert folder.is_dir() and not (folder/'munit').exists()
    subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',extra['filename']],cwd=folder,check=True)
    (folder/('munit-'+extra['commit'])).rename(folder/'munit')
    assert (folder/'munit/meson.build').is_file()
    wrap=folder/'munit.wrap';before=wrap.read_bytes();text=before.decode();assert text.count('revision=head')==1
    wrap.write_text(text.replace('revision=head','revision='+extra['commit']))
    patches.append({'path':'subprojects/munit.wrap','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(wrap.read_bytes()).hexdigest(),'reason':'Freeze existing upstream test-only moving revision to exact supplied immutable local source; no C/tests/assertion changes'})
if row['name']=='shared-mime-info':
    assert extra['name']=='xdgmime-tests'
    subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',extra['filename']],cwd=source/'subprojects',check=True)
    (source/'subprojects'/('xdgmime-'+extra['commit'])).rename(source/'subprojects/xdgmime')
    path=source/'tests/meson.build';before=path.read_bytes();text=before.decode()
    old="args: meson.current_source_dir() / 'mime-db-tests',";assert text.count(old)==1
    text=text.replace(old,"args: '/build/mime-db-tests',");path.write_text(text)
    patches.append({'path':'tests/meson.build','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reason':'Writable generated MIME cache test fixture under private /build; expected XML/tests unchanged'})
if row['name']=='llvm':
    import re
    assert extra['name']=='llvm-upstream-fix'
    subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',extra['filename'],'--verify-only'],check=True)
    patch_path=base/extra['filename'];body=patch_path.read_text()
    paths=re.findall(r'^[+][+][+] b/(.+)$',body,re.M)
    assert len(paths)==14 and all(p.startswith('llvm/') and '..' not in Path(p).parts for p in paths)
    before={p:hashlib.sha256((source/p).read_bytes()).hexdigest() if (source/p).exists() else None for p in paths}
    subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1','-i',str(patch_path)],cwd=source,check=True)
    patches.extend({'path':p,'before_sha256':before[p],'after_sha256':hashlib.sha256((source/p).read_bytes()).hexdigest(),'patch_sha256':extra['sha256']} for p in paths)
    path=source/'llvm/utils/FileCheck/CMakeLists.txt';data=path.read_bytes();text=data.decode();assert text.count('utility')==1
    path.write_text(text.replace('utility','tool'))
    patches.append({'path':'llvm/utils/FileCheck/CMakeLists.txt','before_sha256':hashlib.sha256(data).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reference':'BLFS13.1 install required FileCheck tool'})
    for path in source.rglob('*'):
        if not path.is_file() or path.is_symlink():continue
        with path.open('rb') as f:first=f.readline(4096)
        if re.fullmatch(rb'#![^\\n]*python\\r?\\n',first):
            before=path.read_bytes();after=first.rstrip().removesuffix(b'python')+b'python3\\n'+before[len(first):];path.write_bytes(after)
            patches.append({'path':str(path.relative_to(source)),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'reference':'BLFS13.1 Python3 shebang selection'})
if row['name']=='freetype':
    import re
    for relative in ['modules.cfg','include/freetype/config/ftoption.h']:
        path=source/relative;before=path.read_bytes();text=before.decode()
        if relative=='modules.cfg':
            text,count=re.subn(r'^# (AUX_MODULES [+]= (?:gxvalid|otvalid))$',lambda match:match.group(1),text,flags=re.M);assert count==2
        else:
            old='/* #define FT_CONFIG_OPTION_SUBPIXEL_RENDERING */'
            assert text.count(old)==1;text=text.replace(old,'#define FT_CONFIG_OPTION_SUBPIXEL_RENDERING')
        path.write_text(text)
        patches.append({'path':relative,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reference':'BLFS13.1 general/freetype2.html'})
if row['name'] in ('libevdev','libinput'):
    import shutil,xml.etree.ElementTree as ET
    sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
    from verify_stage import inspect_stage
    prior=base/'phase2/work/libfyaml-1';sdk=prior/'test-sdk';output=source/'toddy-test-sdk'
    assert sdk.is_dir() and not output.exists(),'Reuse qualified Check0.15.2 SDK; do not rebuild accepted libfyaml'
    results=json.loads((prior/'test-results.json').read_text())
    cases=ET.parse(prior/'check-ctest.xml').getroot().findall('.//testcase')
    assert len(cases)==results['check_sdk_ctest_cases']==9
    assert all(not any(x.find(tag) is not None for tag in ['failure','error','skipped']) for x in cases)
    check=next(x for x in json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components'] if x['name']=='check')
    assert check['version']=='0.15.2'
    with (base/check['filename']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==check['sha256']
    for filename in ['libcheck.so.0.15.2','libcheck.a']:
        assert hashlib.sha256((sdk/'lib'/filename).read_bytes()).hexdigest()==hashlib.sha256((prior/'check-compile/src'/filename).read_bytes()).hexdigest()
    sdk_manifest=inspect_stage(sdk);shutil.copytree(sdk,output,symlinks=True)
    assert inspect_stage(output)==sdk_manifest==inspect_stage(sdk)
    private_sdk={'scope':'Reused qualified private native test SDK only; not installed or a runtime dependency',
                 'source':check,'upstream_sdk_cases_reused':9,'manifest':sdk_manifest,
                 'ctest_evidence_sha256':hashlib.sha256((prior/'check-ctest.xml').read_bytes()).hexdigest()}
(source/'toddy-build.sh').write_text(recipe)
if private_bus is not None:(source/'toddy-private-bus.py').write_text(private_bus)
receipt={'source_sha256':row['sha256'],'reference':row['reference'],
         'book_page_sha256':row.get('book_page_sha256'),'source_patches':patches,
         'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()}
if extra is not None:receipt['extra_source']=extra
if row['name'] in ('libevdev','libinput'):receipt['private_test_sdk']=private_sdk
if probe is not None:
    (source/probe_filename).write_text(probe)
    receipt['probe_sha256']=hashlib.sha256(probe.encode()).hexdigest()
(source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+'\\n')
work.mkdir();os.chown(work,101,101)
print(json.dumps(receipt))
'''
    prefix=ROOT/'.local/phase2'/(NAME+'-input'+receipt_suffix)
    with prefix.with_suffix('.log').open('xb') as log:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=data,stdout=log,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n')
    raise SystemExit(result.returncode)
