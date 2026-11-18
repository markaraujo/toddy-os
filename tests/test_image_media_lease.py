"""Actual inherited kernel lease fixture; no namespace/mount/VM execution."""
import grp,os,stat,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MediaLeaseTests(unittest.TestCase):
 def test_only_exact_ubuntu_log_parent_exception(self):
  sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
  import image_media as media
  class Info:
   st_uid=0
   st_gid=grp.getgrnam('syslog').gr_gid
   st_mode=stat.S_IFDIR|0o775
  info=Info()
  self.assertTrue(media.trusted_log_parent(Path('/var/log'),info))
  self.assertFalse(media.trusted_log_parent(Path('/var/log/toddy'),info))
  info.st_gid=0
  self.assertFalse(media.trusted_log_parent(Path('/var/log'),info))
  info.st_gid=grp.getgrnam('syslog').gr_gid
  info.st_mode=stat.S_IFDIR|0o777
  self.assertFalse(media.trusted_log_parent(Path('/var/log'),info))
 def test_fixed_builder_route_closes_only_input_not_global_lease(self):
  source=(ROOT/'scripts/build/phase2/image_native.sh').read_text()
  subprocess.run(['/bin/bash','-n',str(ROOT/'scripts/build/phase2/image_native.sh')],check=True)
  for action in ('compress','initramfs','iso'):self.assertIn('media-'+action,source)
  route=source.rsplit('    media-compress|',1)[-1].split('    *)',1)[0]
  self.assertIn('image_media.py "$action" 8<&-',route);self.assertNotIn('chroot',route);self.assertNotIn('9>&-',route)
 def test_actual_inherited_exclusive_shared_wrong_inode(self):
  program=r'''
import fcntl,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import image_media as m
m.BUILD=Path(sys.argv[2]);path=m.BUILD/'build.lock'
fd=os.open(path,os.O_RDWR|os.O_CREAT,0o600)
fcntl.flock(fd,fcntl.LOCK_EX if sys.argv[3]!='shared' else fcntl.LOCK_SH)
os.dup2(fd,9)
# Only synthetic fixture ancestors are writable/unowned; real file/fd identity,
# kernel FLOCK and owner/type/mode checks remain actual.
original=Path.lstat
class Parent:
 st_mode=0o40755;st_uid=0
Path.lstat=lambda self: original(self) if self==path else Parent()
if sys.argv[3]=='wrong':
 other=os.open(m.BUILD/'other',os.O_RDWR|os.O_CREAT,0o600);os.dup2(other,9)
try:
 assert m.inherited_media_lease()==9
 assert os.fstat(9).st_ino==path.stat().st_ino
 assert sys.argv[3]=='exclusive'
except ValueError:
 assert sys.argv[3]!='exclusive'
'''
  # Production owner requirement remains root0; run owner fixtures only when
  # root, otherwise synthetic input metadata changes owner only, not FD/locks.
  if os.getuid()!=0:
   program=program.replace("if sys.argv[3]=='wrong':","real_lstat=Path.lstat\ndef file_stat(self):\n info=real_lstat(self)\n if self==path:\n  class Owner:\n   st_uid=0\n   def __getattr__(self,name):return getattr(info,name)\n  return Owner()\n return info\nPath.lstat=file_stat\nif sys.argv[3]=='wrong':")
  for mode in ('exclusive','shared','wrong'):
   with tempfile.TemporaryDirectory() as folder:
    result=subprocess.run([sys.executable,'-I','-c',program,str(ROOT/'scripts/build/phase2'),folder,mode],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
