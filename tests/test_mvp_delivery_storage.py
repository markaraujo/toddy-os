"""ADR-0251 changes only the explicit MVP host floor, never target/standard floors."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/host'))
import mvp_delivery_storage as storage
import native_installer_live as live
import installed_owner_boot as installed
class MVPHostStorageTests(unittest.TestCase):
 def test_fixed_profiles_and_no_numeric_override(self):
  self.assertEqual(storage.host_floor(),100*1024**3+512*1024**2)
  self.assertEqual(storage.host_floor(True),60*1024**3+512*1024**2)
  for value in ('mvp',60,1,None):
   with self.assertRaises(ValueError):storage.host_floor(value)
 def test_actual_live_and_boot_admission_select_profile(self):
  for mvp in (False,True):
   floor=storage.host_floor(mvp)
   with patch.object(live,'MVP',mvp),patch.object(installed,'MVP',mvp):
    threshold=floor+2*1024**3+4*1024**3
    self.assertTrue(live.admission(threshold,{'root_storage_bound_bytes':1024**3}))
    self.assertFalse(live.admission(threshold-1,{'root_storage_bound_bytes':1024**3}))
    self.assertTrue(installed.capacity_admitted(floor+3*1024**3,1024**3))
    self.assertFalse(installed.capacity_admitted(floor+3*1024**3-1,1024**3))
    self.assertTrue(installed.capacity_stop_required(floor+installed.STOP_HEADROOM-1))
 def test_transfers_default_standard_and_later_explicit_mvp(self):
  source=(ROOT/'scripts/host/collect_package_export2.py').read_text()
  self.assertIn('host_floor(generation in (3,4,5,6,7,8))',source)
  self.assertEqual(installed.HOST_FLOOR,storage.STANDARD_HOST_FLOOR)
  self.assertEqual(live.HOST_FLOOR,storage.STANDARD_HOST_FLOOR)
if __name__=='__main__':unittest.main()
