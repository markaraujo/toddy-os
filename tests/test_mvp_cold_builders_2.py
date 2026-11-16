"""Fixed data-only second pair; no compression/unlink or VM operation."""
import hashlib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/host'))
import phase2_mvp_cold_builders as original
ORIGINAL=dict(original.PROFILES)
import phase2_mvp_cold_builders_2 as second

class SecondColdBuilderTests(unittest.TestCase):
 def test_second_pair_is_small_fixed_and_cannot_rebind_first_pair(self):
  self.assertEqual(original.PROFILES,ORIGINAL)
  self.assertEqual(set(second.PROFILES),{'h07-final-base-builder.qcow2','h09-boot-ready-builder.qcow2'})
  self.assertEqual(sum(row['allocated'] for row in second.PROFILES.values()),12957429760)
  for name,row in second.PROFILES.items():
   self.assertLess(row['bytes'],12*1024**3);self.assertNotIn('target',name)
   self.assertEqual(len(row['manifest_sha256']),64);self.assertEqual(len(row['sha256']),64)
  self.assertIsNot(second._guard,original)
  self.assertEqual(hashlib.sha256(second.SOURCE.read_bytes()).hexdigest(),second.SOURCE_SHA256)
 def test_shared_protocol_has_distinct_context_and_same_protected_guards(self):
  source=(ROOT/'scripts/host/phase2_compress_cold_checkpoints.py').read_text()
  self.assertIn('cold-checkpoint-compression-mvp-builders-2',source)
  self.assertIn("mvp=args.profile in ('mvp-builders','mvp-builders-2')",source)
  for text in ('F_OFD_SETLK','verify_gzip(part','strict.image_identity(p)','strict.manifest(name)','floor=RESERVE+512*1024**2','os.fsync(directory)'):
   self.assertIn(text,source)

if __name__=='__main__':unittest.main()
