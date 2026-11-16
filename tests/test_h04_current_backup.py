"""Current-byte hash and fixed-scope fixtures; no real backup compression/retire."""
import hashlib,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/host'))
import phase2_h04_current_cold_backup as p
class CurrentBackupTests(unittest.TestCase):
 def test_fresh_full_readonly_sha_is_not_a_historical_claim_and_resets_fd(self):
  body=b'current opaque fixture'+b'\0'*8192
  with tempfile.TemporaryFile() as stream:
   stream.write(body);stream.flush();info=os.fstat(stream.fileno())
   proof=p.current_sha(stream.fileno(),info)
   self.assertEqual(proof['sha256'],hashlib.sha256(body).hexdigest());self.assertEqual(proof['bytes'],len(body))
   self.assertFalse(proof['historical_integrity_claimed']);self.assertEqual(os.lseek(stream.fileno(),0,os.SEEK_CUR),0)
 def test_current_profile_has_no_fabricated_original_manifest_or_digest(self):
  self.assertEqual(set(p.PROFILES),{'h04-target.qcow2'});row=p.PROFILES['h04-target.qcow2']
  self.assertIsNone(row['backing']);self.assertNotIn('sha256',row);self.assertNotIn('manifest_sha256',row)
  self.assertEqual(row['bytes'],8805875712);self.assertEqual(row['allocated'],8784470016)
  with self.assertRaises(ValueError):p.image_identity(ROOT/'unrelated.qcow2')
 def test_absolute_graph_delegation_restores_historical_profiles_on_refusal(self):
  original=p.graph_guard.PROFILES
  def fail():
   self.assertIs(p.graph_guard.PROFILES,p.PROFILES);raise ValueError('fixture unknown backing')
  with patch.object(p.graph_guard,'graph',side_effect=fail):
   with self.assertRaises(ValueError):p.graph()
  self.assertIs(p.graph_guard.PROFILES,original)
