"""Small graph/receipt fixtures; no checkpoint compression/deletion or VM start."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/host'))
import phase2_mvp_cold_builders as p
class MVPColdBuildersTests(unittest.TestCase):
 def test_only_two_small_builder_names_and_exact_receipt_sha(self):
  self.assertEqual(set(p.PROFILES),{'h07-native-crypto-builder.qcow2','h07-native-services-builder.qcow2'})
  for row in p.PROFILES.values():
   self.assertLess(row['bytes'],12*1024**3);self.assertEqual(len(row['sha256']),64);self.assertEqual(len(row['manifest_sha256']),64)
  self.assertEqual(sum(row['allocated'] for row in p.PROFILES.values()),12345389056)
 def test_absolute_backings_never_inferred_from_basename(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);vm=root/'.local/vm';(vm/'checkpoints').mkdir(parents=True);image=vm/'checkpoints/source.qcow2';image.write_bytes(b'fixture')
   base=vm/'builder-base.img';base.write_bytes(b'base')
   with patch.object(p,'ROOT',root):
    self.assertEqual(p.resolve_backing(image,'/vm/builder-base.img'),base)
    with self.assertRaises((ValueError,FileNotFoundError)):p.resolve_backing(image,'/unmapped/builder-base.img')
    escaped=vm/'alias.img';escaped.symlink_to(Path(temporary).parent/'unrelated')
    with self.assertRaises(ValueError):p.canonical(escaped)
 def test_mismatched_historical_manifest_refuses(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);folder=root/'.local/vm/checkpoints';folder.mkdir(parents=True)
   name=next(iter(p.PROFILES));(folder/p.PROFILES[name]['manifest']).write_text('{}')
   with patch.object(p,'ROOT',root):
    with self.assertRaisesRegex(ValueError,'manifest changed'):p.manifest(name)
 def test_selected_inode_change_refuses_without_reading_image_bytes(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);folder=root/'.local/vm/checkpoints';folder.mkdir(parents=True);name=next(iter(p.PROFILES));path=folder/name;path.write_bytes(b'not original');path.chmod(0o644)
   with patch.object(p,'ROOT',root),patch.object(p,'manifest'):
    with self.assertRaisesRegex(ValueError,'inode/metadata'):p.image_identity(path)
