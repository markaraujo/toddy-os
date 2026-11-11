"""Reconcile completed native recovery; GRUB does not emit an assumed Booting line."""
from pathlib import Path
import hashlib,json,re,subprocess
import phase2_vm
from phase2_native_report import decode
c=phase2_vm.ROOT/'.local/phase2/native-desktop-recovery-runtime-1'
r=json.loads((c/'result.json').read_text());assert r['phase']=='native-stopped' and r['container_final_state']['Running'] is False
actual=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',r['container_id']],text=True));assert actual['Running'] is False and actual['ExitCode']==0
source=phase2_vm.ROOT/'.local/phase2/native-desktop-reboot-runtime-1/target.qcow2';assert phase2_vm.backing_identity(source)==r['source_identity']
menu=json.loads((c/'recovery-menu-selection.json').read_text());assert menu['selected']
serial=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',(c/'serial.log').read_text(errors='replace'));assert '*Toddy OS, Linux 7.1.8-toddy (foundation recovery)' in serial
raw=(c/'native-evidence.log').read_text();report,summary,recovered=decode(raw);assert report['all_selected_exits_zero'] and summary['all_selected_exits_zero']
assert report['foundation_recovery_kernel'] and report['running_config_sha256']=='3ad1bf1ce1e1a844ac35a5c0c9769536bff6e30d9ae75dd20ee2341a9f544e0e'
(c/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
r.update(phase='native-desktop-recovery-verified',native_selected_passed=True,backing_unchanged=True,summary=summary,recovered_protocol_markers=recovered,actual_grub_recovery_selection=menu,dedicated_evidence_sha256=hashlib.sha256(raw.encode()).hexdigest(),collector_reconciliation='Original collector failed only on nonexistent literal Booting line. Actual highlighted GRUB selection and different running foundation config prove selected entry. No boot/write repeated.')
p=c/'result.json.part';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');p.replace(c/'result.json');print(json.dumps({'phase':r['phase'],'actual_running_config':report['running_config_sha256'],'native_report_sha256':summary['report_sha256'],'no_boot_replay':True}))
