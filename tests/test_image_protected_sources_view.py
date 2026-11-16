"""Real FD/flock/heredoc fixtures + namespace contracts; no mount/VM execution."""
import hashlib,json,os,re,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/'scripts/build/phase2/image_native.sh'

class ProtectedViewTests(unittest.TestCase):
 def test_stage_anchored_before_private_parent_and_exec_nosuid_nodev_child(self):
  source=WRAPPER.read_text();subprocess.run(['/bin/bash','-n',str(WRAPPER)],check=True)
  anchor=source.index('/usr/bin/mount --bind "$stage" "$anchor"')
  parent=source.index('/usr/bin/mount -t tmpfs -o size=1m,mode=0755,nosuid,nodev,noexec')
  child=source.index('/usr/bin/mount --bind "$anchor" "$stage"')
  self.assertLess(source.index('trap cleanup EXIT'),anchor);self.assertLess(anchor,parent);self.assertLess(parent,child)
  self.assertIn('remount,bind,rw,exec,nosuid,nodev "$stage"',source)
  self.assertIn('[[ ,$options, != *,noexec,* ]]',source)
  self.assertIn("legacy_pin=$(stat -c '%d:%i:%u:%g:%a'",source)
  self.assertIn('== "$stage_pin"',source);self.assertIn('== 0:0:755',source)
  self.assertNotRegex(source,r'\b(?:chmod|chown)\b');self.assertNotRegex(source,r'umount[^\n]*(?:--lazy| -l| -f)')
  self.assertNotRegex(source,r'\brm\s+-[a-z]*r')
 def test_cleanup_order_and_placeholder_pin_never_remove_actual_stage(self):
  source=WRAPPER.read_text();cleanup=source.split('cleanup() {',1)[1].split('trap cleanup EXIT',1)[0]
  positions=[cleanup.index('/usr/bin/umount "$'+name+'"') for name in ('binding','stage','sources','anchor')]
  self.assertEqual(positions,sorted(positions))
  self.assertLess(cleanup.index('== "$placeholder_pin"'),cleanup.index('rmdir "$stage"'))
  self.assertLess(cleanup.index('rmdir "$stage"'),cleanup.index('/usr/bin/umount "$sources"'))
  self.assertIn('$sources_mounted == 1',cleanup);self.assertIn('== "$legacy_pin"',cleanup)
  self.assertIn('rmdir "$anchor"',cleanup)
 def test_only_exact_actions_route_with_original_input_and_raw_output(self):
  source=WRAPPER.read_text()
  self.assertLess(source.index('exec 8<&0'),source.index("<<'NAMESPACE'"))
  for profile in ('offline','live'):
   for action in ('inspect','export','receipt','metadata','retire'):self.assertIn('custody-'+profile+'-'+action,source)
  self.assertIn('"$action" <&8 8<&-',source);self.assertNotIn('eval ',source);self.assertIn('unshare --mount --propagation private /usr/bin/env -i',source)
  self.assertIn('image_assemble.py "$1" 8<&-',source)
  self.assertNotIn('flock -n 9',source.split("<<'NAMESPACE'",1)[1])
  if os.getuid()!=0:
   result=subprocess.run(['/bin/bash',str(WRAPPER),'custody-live-retire'],input=b'{}',capture_output=True,timeout=5)
   self.assertNotEqual(result.returncode,0);self.assertNotIn(b'mount:',result.stderr)
 def test_original_binary_stdin_survives_heredoc_without_becoming_code(self):
  data=b'{"proof":"$(false)"}\nNAMESPACE\nINNER\n\x00binary\xff\n'
  code="""set -euo pipefail
exec 8<&0
/bin/bash -s <<'INNER'
set -euo pipefail
python3 -c 'import hashlib,sys;print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())' <&8 8<&-
INNER
"""
  result=subprocess.run(['/bin/bash','-c',code],input=data,capture_output=True,check=True)
  self.assertEqual(result.stdout.decode().strip(),hashlib.sha256(data).hexdigest())
 def test_inherited_exclusive_fd9_reused_without_reacquire_and_read_lock_refused(self):
  program=r'''
import fcntl,json,os,sys
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2]]
import candidate_root_custody as c
c.LOCK=Path(sys.argv[3]);c.secured=lambda path:Path(path) # synthetic owner only
fd=os.open(c.LOCK,os.O_RDWR|os.O_CREAT,0o600)
flock=fcntl.flock
flock(fd,fcntl.LOCK_EX if sys.argv[4]=='exclusive' else fcntl.LOCK_SH)
if fd!=9:os.dup2(fd,9)
c.fcntl.flock=lambda *args:(_ for _ in ()).throw(AssertionError('reacquire forbidden'))
try:
 with c.operation_lease() as inherited:
  assert inherited==9 and os.fstat(9).st_ino==c.LOCK.stat().st_ino
 assert os.fstat(9).st_ino==c.LOCK.stat().st_ino
 print('exclusive-reused-and-retained')
except ValueError as error:
 assert sys.argv[4]=='shared' and 'exclusive_global_lease_required' in str(error)
 print('shared-refused-without-upgrade')
'''
  with tempfile.TemporaryDirectory() as temporary:
   for kind,expected in [('exclusive','exclusive-reused-and-retained'),('shared','shared-refused-without-upgrade')]:
    result=subprocess.run([sys.executable,'-I','-c',program,str(ROOT/'scripts/build/phase2'),str(ROOT),str(Path(temporary)/kind),kind],capture_output=True,text=True,timeout=10)
    self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),expected)

if __name__=='__main__':unittest.main()
