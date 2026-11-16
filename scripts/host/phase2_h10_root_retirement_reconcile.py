#!/usr/bin/env python3
"""Reverify real H10 gzip custody and reconcile its already removed guest root."""
import fcntl,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'build/phase2')]
import phase2_candidate_root_custody as host
import h10_root_retirement_reconcile as fixed


def main():
    if sys.argv[1:] or os.geteuid()==0:raise ValueError('fixed_unprivileged_H10_reconciliation_command')
    host.configure('h10-expanded');context=host.CONTEXT;output=context/'postcondition-reconciliation-1.json'
    if os.path.lexists(output):raise ValueError('preserve_H10_existing_companion')
    with (host.vm.VM/'native-boot-test.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);identity=host.candidate.owned();host.candidate.bases()
        receipt=context/'host-verified.json';metadata=context/'source-metadata.json'
        if host.archive.sha(receipt)!=fixed.HOST_RECEIPT or host.archive.sha(metadata)!=fixed.METADATA:raise ValueError('exact_actual_H10_host_receipt_metadata_required')
        state=json.loads(receipt.read_bytes());image=json.loads(metadata.read_bytes());original=state['host_proof']
        if state.get('state')!='complete-member-and-decompression-verified' or state.get('guest_helper_sha256')!=fixed.OLD_PRODUCER or state.get('archive_verifier_sha256')!=fixed.ARCHIVE_VERIFIER or state.get('protected_view_driver_sha256')!=fixed.OLD_DRIVER:raise ValueError('original_actual_H10_producers_required')
        proof=host.verify_compressed(context/host.ARCHIVE_NAME,image,{'tar_sha256':original['tar_sha256'],'tar_bytes':original['tar_bytes']})
        if proof!=original or proof['compressed_sha256']!=fixed.COMPRESSED:raise ValueError('actual_H10_gzip_reverification_differs')
        proof['host_receipt_sha256']=fixed.HOST_RECEIPT
        host.same_guest(identity)
        packet={'version':1,'proof':proof,'metadata_sha256':fixed.METADATA}
        command=[*host.candidate.ssh(),'/usr/bin/python3 -B -I /opt/toddy-build/scripts/build/phase2/h10_root_retirement_reconcile.py']
        result=subprocess.run(command,input=host.archive.encoded(packet),capture_output=True,check=True,timeout=1800)
        if len(result.stdout)>65536:raise ValueError('bounded_actual_H10_companion_required')
        value=json.loads(result.stdout)
        if value.get('state')!='completed-postcondition-reconciliation' or value.get('original_intent_sha256')!=fixed.OLD_INTENT or value.get('host_proof')!=proof or value.get('root_removed') is not True or value.get('removal_replayed') is not False:raise ValueError('actual_H10_companion_binding_required')
        host.same_guest(identity);host.save(output,value);print(host.archive.encoded({'state':value['state'],'context':str(context),'actual_guest_free_gain_bytes':value['actual_guest_free_gain_bytes'],'old_state_preserved':True}).decode(),end='')

if __name__=='__main__':main()
