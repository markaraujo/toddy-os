"""Read-only postcondition/source fixtures; no VM, deletion or native acceptance."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts/build/phase2')]
import h10_root_retirement_reconcile as fixed

class ReconciliationTests(unittest.TestCase):
 def test_original_driver_is_pinned_and_only_fixed_route_is_added_in_memory(self):
  original=b'#!/bin/bash\nexec 9>/var/log/toddy/build/build.lock\nexec 8<&0\ncase $1 in\n original) ;;\nesac\ncase $1 in\n original) ;;\nesac\n'
  with patch.object(fixed,'OLD_DRIVER',hashlib.sha256(original).hexdigest()):
   result=fixed.pinned_driver(original)
   self.assertEqual(result.count('h10-postcondition-reconcile)'),2)
   self.assertIn(' --inside <&8 8<&-',result)
   self.assertIn('exec 9>/var/log/toddy/build/build.lock',result)
   self.assertIn('exec 8<&0',result)
   with self.assertRaisesRegex(ValueError,'driver_changed'):fixed.pinned_driver(original+b'\n')
 def test_absent_root_full_evidence_and_original_intent_are_required_without_replay(self):
  c=fixed.custody;a=c.archive
  with tempfile.TemporaryDirectory() as directory:
   base=Path(directory);custody=base/'custody';custody.mkdir();root=base/'removed-root';evidence=base/'retained.iso';evidence.write_bytes(b'unchanged fixture')
   metadata=custody/'source-metadata.json';metadata.write_bytes(a.encoded({'entries':{'.':{}},'unique_regular_bytes':3}))
   sha=a.sha(metadata);proof={'version':1,'state':'complete-member-and-decompression-verified','host_receipt_sha256':fixed.HOST_RECEIPT,'compressed_sha256':fixed.COMPRESSED,'metadata_sha256':sha,'tar_sha256':'a'*64,'tar_bytes':1024,'member_proof':{'state':'all-members-bytes-metadata-verified','entries':1,'unique_regular_bytes':3,'xattrs_ACLs_symlinks_hardlink_classes_verified':True,'privileged_extraction_performed':False}}
   state={'state':'root-retirement-intended-no-replay','profile':'h10-expanded','producer_sha256':fixed.OLD_PRODUCER,'archive_verifier_sha256':fixed.ARCHIVE_VERIFIER,'before_free_bytes':fixed.BEFORE_FREE,'root':str(root),'host_proof':proof,'metadata_sha256':sha,'tar_sha256':'a'*64,'tar_bytes':1024,'provenance':{'preserved':{str(evidence):a.sha(evidence)},'preserved_links':{}}}
   path=custody/'custody.json';raw=a.encoded(state);path.write_bytes(raw);packet={'version':1,'proof':proof,'metadata_sha256':sha};limits=[]
   def secured(path,limit=256*1024**2):
    if Path(path)==evidence:limits.append(limit)
    return Path(path)
   with patch.object(c,'configure'),patch.object(c,'STATE',path),patch.object(c,'ARTIFACT',root),patch.object(c,'CUSTODY',custody),patch.object(c,'secured',side_effect=secured),patch.object(c,'read',side_effect=lambda p:json.loads(Path(p).read_bytes())),patch.object(fixed,'METADATA',sha),patch.object(fixed,'OLD_INTENT',a.sha(path)),patch.object(fixed.shutil,'disk_usage',return_value=SimpleNamespace(free=fixed.BEFORE_FREE+4096)):
    result=fixed.check(packet);self.assertFalse(result['removal_replayed']);self.assertTrue(result['old_state_preserved']);self.assertEqual(result['actual_guest_free_gain_bytes'],4096)
    self.assertEqual(limits,[8*1024**3]);self.assertEqual(path.read_bytes(),raw)
    root.mkdir()
    with self.assertRaisesRegex(ValueError,'already_be_absent'):fixed.check(packet)
    root.rmdir();evidence.write_bytes(b'drift')
    with self.assertRaisesRegex(ValueError,'regular_bytes_changed'):fixed.check(packet)
 def test_reconciler_has_no_delete_or_old_state_save_call(self):
  source=Path(fixed.__file__).read_text()
  self.assertNotIn('rmtree(',source);self.assertNotIn('.retire(',source)
  self.assertIn('custody.save(RECEIPT,result)',source)
  self.assertNotIn('save(custody.STATE',source)

if __name__=='__main__':unittest.main()
