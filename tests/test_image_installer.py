"""Real local additive-copy metadata fixtures, no native seal/VM/boot claim."""
import importlib.util,os,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import image_installer as image
import image_media as media
class ImageInstallerTests(unittest.TestCase):
 def test_actual_copy_exact_source_tree_and_only_parent_mtime_change(self):
  with tempfile.TemporaryDirectory() as temporary:
   directory=Path(temporary);root=directory/'root';source=directory/'sealed'
   parent=root/Path(image.PREFIX).parent;parent.mkdir(parents=True)
   (root/'unchanged').write_bytes(b'preserved');source.mkdir(mode=0o700)
   (source/'payload').mkdir(mode=0o700);(source/'payload/archive.deb').write_bytes(b'archive fixture')
   (source/'payload/archive.deb').chmod(0o400)
   before=image.snapshot(root,image.tree_names(root));expected=image.snapshot(source,image.tree_names(source))
   shutil.copytree(source,root/image.PREFIX,copy_function=shutil.copy2)
   after=image.snapshot(root,image.tree_names(root))
   added=image.additive_delta(before,after,expected)
   self.assertEqual(added[image.PREFIX+'/payload/archive.deb']['sha256'],expected['entries']['payload/archive.deb']['sha256'])
   (root/'unchanged').write_bytes(b'outside mutation')
   with self.assertRaisesRegex(ValueError,'existing image path'):image.additive_delta(before,image.snapshot(root,image.tree_names(root)),expected)
 def test_installable_mvp_media_generations_preserve_first_desktop_iso(self):
  names=('MVP','IMAGE','JOURNAL','COMPRESSION','INITRAMFS','MEDIA','PROJECTION');saved={name:getattr(media,name) for name in names}
  with patch.multiple(media,**saved):
   media.configure_mvp();desktop={name:getattr(media,name) for name in ('JOURNAL','COMPRESSION','INITRAMFS','MEDIA')}
   media.configure_mvp(installer=True)
   for name,path in desktop.items():self.assertNotEqual(getattr(media,name),path)
   self.assertEqual(media.JOURNAL.parent.name,'evidence-installer')
   self.assertEqual(media.IMAGE.name,'mvp-live-root-2')
 def test_wrapper_contains_only_fixed_source_qualification_and_media_actions(self):
  text=(ROOT/'scripts/build/phase2/image_native.sh').read_text()
  for action in ('seal-mvp-installer','embed-mvp-installer','media-mvp-installer-compress','media-mvp-installer-initramfs','media-mvp-installer-iso'):self.assertIn(action,text)
  self.assertIn('image_installer.py "$operation" 8<&-',text)
