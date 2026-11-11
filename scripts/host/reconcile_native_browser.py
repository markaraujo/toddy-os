#!/usr/bin/env python3
"""Read-only reconciliation of captured native Web Content rows; no runtime replay."""
from pathlib import Path
import hashlib,json,subprocess,sys
import phase2_vm


def reconcile(context):
    state=json.loads((context/'result.json').read_text())
    raw=json.loads((context/'native-report.json').read_text())
    digest=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()
    assert state['phase']=='native-report-recorded' and state['backing_unchanged']
    assert digest==state['summary']['report_sha256']
    assert not raw['all_selected_exits_zero'] and raw['error']=={'type':'AssertionError','message':'Actual Web Content sandbox status incomplete'}
    actual=json.loads(subprocess.check_output(['docker','inspect',state['container_id']],text=True))[0]
    assert not actual['State']['Running'] and actual['State']['ExitCode']==0
    assert actual['Config']['Labels']['toddy.boot-test']==state['run_id']
    assert phase2_vm.backing_identity(phase2_vm.WORK/'lfs-target.qcow2')==state['source_identity']
    assert raw['default_target']['stdout'].strip()=='graphical.target'
    assert raw['automatic_gdm']['exit']==raw['graphical_target']['exit']==0
    assert raw['automatic_gdm']['stdout'].strip()==raw['graphical_target']['stdout'].strip()=='active'
    assert 'systemd.unit=' not in raw['kernel_commandline']
    assert raw['owner_session']['properties']=={'Class':'user','Name':'toddy-preview','Seat':'seat0','State':'active','Type':'wayland'}
    required={'browser-open','input-verified','navigation-verified','restart-verified','tls-verified','offline-verified','stop-verified','responsive-verified'}
    assert required==set(raw['ui_phase_annotations']) and raw['host_requested_finish']
    assert raw['exit_between_launches'] and raw['new_process_after_exit'] and raw['network_off_observed']
    assert any(e.get('path')=='/' for e in raw['http_events'])
    assert any(e.get('path')=='/second.html' for e in raw['http_events'])
    assert any(e['event']=='slow-cancelled' for e in raw['http_events'])
    assert not any(e['event']=='slow-deadline-not-success' for e in raw['http_events'])
    mains=[r for r in raw['final_main'] if r['name'] in ['firefox','firefox-bin']]
    content=[r for r in raw['final_main'] if r['name'] in ['Web Content','Isolated Web Co']]
    assert len(mains)==1 and content
    assert all(r['uid']==12402 and r['NoNewPrivs']=='1' and r['Seccomp']=='2' and int(r['CapEff'],16)==0 for r in content)
    assert mains[0]['pid']!=raw['main_processes_seen'][0]['pid']
    assert raw['gdm_stop']['exit']==0 and raw['schema_unchanged']
    return {'scope':'Captured native default graphical boot, normal GDM owner, browser interaction and process sandbox, reconciled without runtime replay. UI observations require linked unchanged scanouts. No whole B02, physical hardware or ISO acceptance.',
            'input_commit':state['commit'],'probe_sha256':state['probe_sha256'],'original_report_sha256':digest,
            'original_aggregate_passed':False,'reconciled_selected_passed':True,
            'collector_correction':'Firefox rewrites child argv. Select exact observed comm names after original executable/UID guards. Historical child start_ticks omitted because comm spaces invalidated naive stat field indexing.',
            'default_graphical_boot':True,'normal_wayland_owner':raw['owner_session'],
            'main_process':mains[0],'previous_process_exit_observed':True,'profile_value_after_reopen':'Observed in scanout11; normal process exit/reopen separately observed by root probe.',
            'content_processes':[{k:v for k,v in r.items() if k!='start_ticks'} for r in content],
            'http_events':raw['http_events'],'ui_phases':raw['ui_phase_annotations'],
            'network_off_observed':True,'gdm_stop_exit':0,'schema_unchanged':True,'backing_unchanged':True,
            'limitations':['Virtual software rendering, no physical GPU/network/audio proof.','Unqualified official branding is not enabled; upstream calls this build Nightly.','EN/PT text observed. Missing CJK/Arabic glyphs on external example page remain outside this EN/PT check.','Sandbox proof covers actual Web Content NNP/seccomp/capabilities, not all attack surfaces.']}


if __name__=='__main__':
    assert len(sys.argv)==2
    print(json.dumps(reconcile(Path(sys.argv[1])),indent=2))
