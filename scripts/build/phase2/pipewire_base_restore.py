#!/usr/bin/env python3
"""Exact failed PipeWire revision2 recovery; no dependency retarget or apt repair."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import pipewire_tools_native as frozen
from package_backend import PackageBackend
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');BUILD=Path('/var/log/toddy/build');LOG=Path('/var/log/toddy/phase2')
STEP='b09-pipewire-base-restore-1';INSTALL='scripts/build/phase2/pipewire_base_restore_install.sh';CHECK='scripts/build/phase2/pipewire_base_restore_check.sh'
RECEIPT=LOG/'pipewire-base-restore-1.json'
REJECTED_ARCHIVE_SHA='bf08b0426e4596eed1363fb2a64889ab31b4ecafdb58bc3f92ebb5d91a915a55'
REJECTED_RECORD_SHA='8302491a6fae68d1a443b33e8d9bd884be19719520fb89de9e693da56b4d9c3c'
FAILED_RECEIPT_SHA='994c633373d1c15ded40075c6ff1320da5bef78eb4aa44a4d9d1fe533b842cc6'
FAILED_MANIFEST_SHA='4166be95d52f06a4b623d0d89b0765c6d127c40f765e44417c8a833097c14f58'
APT_STDOUT_SHA='70c4dfc0c43cfd39013cfb79db7dd8e00a8e33b5fa3cac1caf4a4980a8c118ea'
APT_STDERR_SHA='23285fc66d3ae2040e5c6a7e41b568120450ae4917f195546e48ca9ab9f69bbc'
REVERSE_PINS={'gnome-shell': {'version': '50.4-1+toddy1', 'architecture': 'amd64', 'record_sha256': '0c8a720c53ee08c506e86e0cf092ff194c36a6cf695ce64d05e168d1bba39a00', 'depends_sha256': 'c80dc01c10a29870b13b12cc5129c5b73187b389196acabaac6bdcbe4409f4a7'}, 'mutter': {'version': '50.4-1+toddy1', 'architecture': 'amd64', 'record_sha256': 'da91b7dc37ad2c5d8eeafafb54b224126af63dc9bcbd798fda2685efc76de05a', 'depends_sha256': '583dbe94d7c30de759b88733d64de77d4c271bf20cea4ed7775ac3db697c54ef'}, 'toddy-desktop-audio': {'version': '0.2.0-1+toddy1', 'architecture': 'all', 'record_sha256': 'd1fb57f23de9ccb9496e33709766caa8e5aa977691588ec26b8f689969a9d86f', 'depends_sha256': '299bd0e62048276c2a19d3ce3915bedc63f3a1628c38e03ea48a62c258649987'}, 'wireplumber': {'version': '0.5.15-1+toddy1', 'architecture': 'amd64', 'record_sha256': '818c7751a09fd80340f9f2474cdbd3948084f1a10d0171cfba69e17746f0c0ce', 'depends_sha256': '53304b16ab4bc088f6769cb9691a3ea9c2721d4bd78d508dd71f1ca9325c75a0'}, 'xdg-desktop-portal': {'version': '1.22.1-1+toddy1', 'architecture': 'amd64', 'record_sha256': 'd2c42f0015da36a20951a63554b3dd1354e76e0c168432745c78c6923b518a13', 'depends_sha256': '5991cfaff152c61e3fec92307a505c2f18e94ee0278e0a03b9e1f06df2ae4b7e'}}


def transaction(phase):
    row=json.loads((BUILD/(STEP+'.running.json')).read_bytes())
    if row.get('step')!=STEP or row.get('user')!='root' or row.get('recipe_sha256')!=frozen.digest(ROOT/INSTALL) or row.get('postcheck_sha256')!=frozen.digest(ROOT/CHECK):raise ValueError('pipewire_restore_owned_dispatcher_required')
    if phase=='install' and row.get('recipe_pid') not in (os.getpid(),os.getppid()):raise ValueError('pipewire_restore_dispatcher_pid')
    if phase=='postcheck' and (type(row.get('recipe_exit')) is not int or row['recipe_exit']!=0):raise ValueError('pipewire_restore_native_recipe_not_complete')


def source_inputs():
    return {name:frozen.digest(frozen.regular(ROOT/name)) for name in (INSTALL,CHECK,'scripts/build/phase2/pipewire_base_restore.py')}


def rejected():
    paths={'failed_receipt':BUILD/(frozen.STEP+'.failed.json'),'manifest':BUILD/(frozen.STEP+'.manifest.json'),
        'record':frozen.RECORDS/('pipewire_'+frozen.VERSION+'_amd64.json'),'archive':frozen.CACHE/('pipewire_'+frozen.VERSION+'_amd64.deb')}
    expected={'failed_receipt':FAILED_RECEIPT_SHA,'manifest':FAILED_MANIFEST_SHA,'record':REJECTED_RECORD_SHA,'archive':REJECTED_ARCHIVE_SHA}
    for name,path in paths.items():
        if frozen.digest(frozen.regular(path))!=expected[name]:raise ValueError('pipewire_restore_rejected_custody_changed')
    failed=json.loads(paths['failed_receipt'].read_bytes());row=json.loads(paths['record'].read_bytes())
    if (failed.get('step')!=frozen.STEP or type(failed.get('recipe_exit')) is not int or failed['recipe_exit']!=0 or
            type(failed.get('postcheck_exit')) is not int or failed['postcheck_exit']!=1 or
            row.get('name')!='pipewire' or row.get('version')!=frozen.VERSION or row.get('archive_sha256')!=REJECTED_ARCHIVE_SHA or row.get('installed') is not True or len(row.get('payload',{}))!=660):
        raise ValueError('pipewire_restore_exact_failed_upgrade_required')
    return row,{'step':frozen.STEP,'failed_receipt_sha256':FAILED_RECEIPT_SHA,'manifest_sha256':FAILED_MANIFEST_SHA,
        'archive_sha256':REJECTED_ARCHIVE_SHA,'record_sha256':REJECTED_RECORD_SHA}


def additions(old,rejected):
    expected={'/usr/bin/pw-cat'}|{'/usr/bin/'+name for name in frozen.ALIASES}|{'/usr/share/doc/pipewire/pw-cat-upgrade-source.json'}
    if (len(old['payload'])!=649 or set(rejected['payload'])-set(old['payload'])!=expected or
            any(rejected['payload'].get(name)!=row for name,row in old['payload'].items())):raise ValueError('pipewire_restore_rejected_payload_not_narrow')
    return sorted(expected)


def reverse_pins():
    for name,expected in REVERSE_PINS.items():
        value=frozen.native('/usr/bin/dpkg-query','-W','-f=${Status}\t${Version}\t${Architecture}\t${Depends}',name).split('\t',3)
        if len(value)!=4 or value[:3]!=['install ok installed',expected['version'],expected['architecture']] or hashlib.sha256(value[3].encode()).hexdigest()!=expected['depends_sha256']:
            raise ValueError('pipewire_restore_reverse_dependency_changed')
        record=frozen.regular(frozen.RECORDS/(name+'_'+expected['version']+'_'+expected['architecture']+'.json'))
        if frozen.digest(record)!=expected['record_sha256'] or not re.search(r'(?:^|,\s*)pipewire\s*\(=\s*1\.6\.8-1\+toddy1\)',value[3]):raise ValueError('pipewire_restore_reverse_record_changed')
    return REVERSE_PINS


def apt_before():
    command=['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','HOME=/root','LC_ALL=C','/usr/bin/apt-get','check']
    result=subprocess.run(command,capture_output=True,text=True,timeout=90)
    names=re.findall(r'^ ([a-z0-9+.-]+) : Depends: pipewire \(= 1\.6\.8-1\+toddy1\) but 1\.6\.8-1\+toddy2 is installed$',result.stdout,re.M)
    if result.returncode!=100 or set(names)!=set(REVERSE_PINS) or len(names)!=5 or hashlib.sha256(result.stdout.encode()).hexdigest()!=APT_STDOUT_SHA or hashlib.sha256(result.stderr.encode()).hexdigest()!=APT_STDERR_SHA:raise ValueError('pipewire_restore_only_known_dependency_breakage_required')
    return {'exit':100,'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest(),'known_reverse_pins':sorted(names)}


def restored_checks():
    old,_=frozen.baseline();row,failed=rejected();added=additions(old,row)
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Status} ${Version}','pipewire')!='install ok installed '+frozen.OLD:raise ValueError('pipewire_restore_old_native_version_required')
    frozen.verify_old(TARGET,old['payload']);reverse_pins()
    if any(os.path.lexists(TARGET/name.lstrip('/')) for name in added):raise ValueError('pipewire_restore_added_tool_path_remains')
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Conffiles}','pipewire') or frozen.native('/usr/bin/dpkg','--audit'):raise ValueError('pipewire_restore_database_or_conffiles')
    frozen.native('/usr/bin/apt-get','check')
    if frozen.native('/usr/bin/pkg-config','--modversion','libpipewire-0.3')!='1.6.8':raise ValueError('pipewire_restore_native_SDK_version')
    return old,failed,added


def install():
    transaction('install')
    if os.path.lexists(RECEIPT) or os.path.lexists(RECEIPT.with_suffix('.part')):raise ValueError('pipewire_restore_existing_outcome_no_replay')
    old,archive=frozen.baseline();row,failed=rejected();added=additions(old,row)
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Status} ${Version}','pipewire')!='install ok installed '+frozen.VERSION:raise ValueError('pipewire_restore_exact_installed_revision2_required')
    frozen.verify_old(TARGET,row['payload']);pins=reverse_pins();apt=apt_before();archive_info=frozen.archive_summary(archive)
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Conffiles}','pipewire') or frozen.native('/usr/bin/dpkg','--audit'):raise ValueError('pipewire_restore_unconfigured_or_conffile_state')
    if shutil.disk_usage(TARGET).free<16*1024**3+512*1024**2+3*archive_info['regular_bytes']:raise ValueError('pipewire_restore_preserve_16gib_reserve')
    backend=PackageBackend()
    if not backend.native or backend.record!=row['packaging_backend']:raise ValueError('pipewire_restore_actual_native_backend_required')
    receipt={'version':1,'state':'native-base-restore-intended-no-replay','failed_upgrade':failed,'reverse_pins':pins,'apt_before':apt,
        'old_archive_sha256':frozen.OLD_ARCHIVE_SHA,'old_record_sha256':frozen.OLD_RECORD_SHA,'source_inputs':source_inputs(),
        'added_paths_to_remove':added,'rejected_payload_entries_verified':660,'old_payload_entries_verified':649}
    frozen.save(RECEIPT,receipt)
    # Explicit exact archived-base restoration, never an APT solver/force repair.
    backend.install(archive)
    restored_checks();receipt['state']='native-base-restored-postcheck-pending';frozen.save(RECEIPT,receipt)


def postcheck():
    transaction('postcheck');receipt=json.loads(frozen.regular(RECEIPT).read_bytes())
    if receipt.get('state')!='native-base-restored-postcheck-pending' or receipt.get('source_inputs')!=source_inputs():raise ValueError('pipewire_restore_receipt_requires_reconciliation')
    old,failed,added=restored_checks()
    if receipt['failed_upgrade']!=failed or receipt['old_record_sha256']!=frozen.OLD_RECORD_SHA or receipt['old_archive_sha256']!=frozen.OLD_ARCHIVE_SHA:raise ValueError('pipewire_restore_bound_failure_changed')
    receipt.update(state='native-pipewire-base-restored',old_payload_unchanged=True,added_paths_absent=added,apt_check_exit=0,
        scope='Exact old native base restored; failed revision2 archive/record/ledger and successful compile2 retained; no new audio tools installed')
    frozen.save(RECEIPT,receipt)


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or sys.argv[1:] not in (['install'],['postcheck']):raise ValueError('pipewire_restore_fixed_guest_root_action')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source "$1"; guard_target','guard',str(ROOT/'scripts/build/target.sh')],check=True)
    if sys.argv[1]=='install':install()
    else:postcheck()

if __name__=='__main__':main()
