import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from boot_config_recovery import render,base_render
class RecoveryMenu(unittest.TestCase):
 def test_preserves_default_and_binds_recovery_to_same_root(self):
  fs='e7726c1a-8f91-445f-96ac-88721b58caf8';part='5e491ca4-ea89-4e55-94b3-cb0b3fcc4694';text=render(fs,part)
  self.assertTrue(text.startswith(base_render(fs,part)));self.assertEqual(text.count('root=PARTUUID='+part),2);self.assertEqual(text.count('set default=0'),1);self.assertEqual(text.count('menuentry '),2);self.assertIn('linux /boot/vmlinuz-7.1.8-toddy-foundation ',text)
 def test_rejects_injected_disk_identifier(self):
  with self.assertRaises(ValueError):render('x\nmenuentry injected','5e491ca4-ea89-4e55-94b3-cb0b3fcc4694')
if __name__=='__main__':unittest.main()
