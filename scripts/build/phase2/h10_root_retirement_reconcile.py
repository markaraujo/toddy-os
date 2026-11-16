#!/usr/bin/env python3
"""Fixed H10 post-delete reconciliation; never replays removal or old state writes."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[2])]
import candidate_root_custody as custody
OLD_PRODUCER='ae3c2764e69a8a408e0f783c84efd15809cb3c415a6b1bc9a763a517e06558ae'
OLD_DRIVER='25bddc51a97572a9233abbeca01cd61011d2792639b42bf2492df4014cc73cf7'
OLD_INTENT='9c80d5faebeddedd149c0771f7a36fa98dc6a3d575b53a0dbc8b176ed0962eca'
HOST_RECEIPT='be9d71a5384033a0a4166678ee2c19a2be66caefa87971fe7059f019cc4a9ef8'
METADATA='67879ed135ec69f0b4e1716fb68103d2b5407581078c15e60fecae298a5d4252'
ARCHIVE_VERIFIER='24d83c060a3d56f4474d303346e393a6adfc7d7361ebb4e573c73ab4e53fc50e'
COMPRESSED='745925261417276875f9bae1df5f09d37612a8a8f4f16e9b6aa8ff67420ef977'
BEFORE_FREE=43430825984
RECEIPT=Path('/var/log/toddy/phase2/h10-expanded-retirement-reconciled-1.json')
ENTRY=Path('/opt/toddy-build/scripts/build/phase2/h10_root_retirement_reconcile.py')


def pinned_driver(source):
    if hashlib.sha256(source).hexdigest()!=OLD_DRIVER:raise ValueError('original_H10_namespace_driver_changed')
    text=source.decode();needle='case $1 in\n'
    if text.count(needle)!=2:raise ValueError('original_namespace_dispatch_shape_changed')
    first,second,third=text.split(needle)
    route='    h10-postcondition-reconcile) /usr/bin/python3 -I '+str(ENTRY)+' --inside <&8 8<&- ;;\n'
    return first+needle+'    h10-postcondition-reconcile) ;;\n'+second+needle+route+third


def check(packet):
    custody.configure('h10-expanded');a=custody.archive
    if (not isinstance(packet,dict) or set(packet)!={'version','proof','metadata_sha256'} or packet['version']!=1 or packet['metadata_sha256']!=METADATA):raise ValueError('fixed_H10_host_proof_required')
    original=custody.secured(custody.STATE,128*1024**2)
    if a.sha(original)!=OLD_INTENT:raise ValueError('exact_original_retirement_intent_required')
    state=custody.read(original);proof=packet['proof']
    if (state.get('state')!='root-retirement-intended-no-replay' or state.get('profile')!='h10-expanded' or state.get('producer_sha256')!=OLD_PRODUCER or state.get('archive_verifier_sha256')!=ARCHIVE_VERIFIER or state.get('before_free_bytes')!=BEFORE_FREE or state.get('root')!=str(custody.ARTIFACT) or state.get('host_proof')!=proof or proof.get('host_receipt_sha256')!=HOST_RECEIPT or proof.get('compressed_sha256')!=COMPRESSED or proof.get('state')!='complete-member-and-decompression-verified'):raise ValueError('original_actual_H10_host_receipt_binding_required')
    if os.path.lexists(custody.ARTIFACT):raise ValueError('H10_root_must_already_be_absent_no_delete')
    metadata=custody.CUSTODY/'source-metadata.json'
    if a.sha(custody.secured(metadata,128*1024**2))!=METADATA or state['metadata_sha256']!=METADATA:raise ValueError('original_H10_raw_metadata_changed')
    image=custody.read(metadata)
    expected={'state':'all-members-bytes-metadata-verified','entries':len(image['entries']),'unique_regular_bytes':image['unique_regular_bytes'],'xattrs_ACLs_symlinks_hardlink_classes_verified':True,'privileged_extraction_performed':False}
    if proof.get('member_proof')!=expected or proof.get('metadata_sha256')!=METADATA or any(proof.get(k)!=state[k] for k in ('tar_sha256','tar_bytes')):raise ValueError('complete_original_H10_raw_member_proof_required')
    for path,sha in state['provenance']['preserved'].items():
        if a.sha(custody.secured(path,8*1024**3))!=sha:raise ValueError('preserved_H10_regular_bytes_changed')
    for path,row in state['provenance'].get('preserved_links',{}).items():
        if custody.preserved_link(Path(path),Path(row['tree']))!=row:raise ValueError('preserved_H10_link_metadata_changed')
    after=shutil.disk_usage(custody.TARGET).free
    if after<=BEFORE_FREE:raise ValueError('actual_positive_H10_free_gain_required')
    if a.sha(original)!=OLD_INTENT or os.path.lexists(custody.ARTIFACT):raise ValueError('original_H10_effect_changed_during_reconciliation')
    return {'version':1,'state':'completed-postcondition-reconciliation','profile':'h10-expanded','root_removed':True,
        'original_intent_sha256':OLD_INTENT,'original_producer_sha256':OLD_PRODUCER,'host_receipt_sha256':HOST_RECEIPT,
        'host_proof':proof,'raw_metadata_sha256':METADATA,'all_preserved_regular_and_links_unchanged':True,
        'before_free_bytes':BEFORE_FREE,'after_free_bytes':after,'actual_guest_free_gain_bytes':after-BEFORE_FREE,
        'old_state_preserved':True,'removal_replayed':False,'new_acceptance_claimed':False}


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or Path(__file__).resolve()!=ENTRY or sys.argv[1:] not in ([],['--inside']):raise ValueError('fixed_root_H10_reconciliation_entry_required')
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536:raise ValueError('bounded_public_host_proof_required')
    packet=json.loads(raw)
    if not sys.argv[1:]:
        custody.configure('h10-expanded')
        if custody.archive.sha(custody.secured(Path(custody.__file__)))!=OLD_PRODUCER:raise ValueError('preserve_original_H10_producer_before_reconciliation')
        driver=custody.secured(custody.ROOT/'scripts/build/phase2/image_native.sh')
        subprocess.run(['/usr/bin/bash','-c',pinned_driver(driver.read_bytes()),'fixed-H10-reconciliation','h10-postcondition-reconcile'],input=raw,check=True)
        return
    os.umask(0o077);custody.validate_lease(9)
    if Path('/proc/self/ns/mnt').readlink()==Path('/proc/1/ns/mnt').readlink():raise ValueError('original_private_namespace_required')
    with custody.operation_lease():
        if list(custody.LOCK.parent.glob('*.running.json')) or (custody.LOCK.parent/'input-sync.running').exists() or custody.unclosed_compiler_jobs(custody.LOG):raise ValueError('preserve_other_native_operation')
        if os.path.lexists(RECEIPT) or os.path.lexists(RECEIPT.with_suffix('.part')):raise ValueError('preserve_existing_or_uncertain_H10_companion')
        result=check(packet);result['reconciler_sha256']=custody.archive.sha(ENTRY)
        custody.save(RECEIPT,result);print(custody.archive.encoded(result).decode(),end='')

if __name__=='__main__':main()
