"""Fixed export4 routing/packet fixtures; no host signing or native execution."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts/host'),str(ROOT/'scripts/build/phase2')]
import collect_package_export2 as collector
import stage_package_export3_signatures as host
import export4_public_signatures as native
class Export4Tests(unittest.TestCase):
 def test_only_fixed_new_routes_preserve_old_defaults(self):
  before=(collector.SOURCE,collector.DESTINATION,host.CONTEXT,host.ASSETS)
  self.assertEqual(collector.fixed_paths(4)[0],'/mnt/lfs/sources/stage/toddy-package-export-4')
  self.assertEqual(collector.fixed_paths(4)[1],ROOT/'.local/phase2/mvp-package-export-4')
  self.assertEqual(host.fixed_context(4),ROOT/'.local/phase2/mvp-package-export-4')
  self.assertEqual(collector.fixed_paths(),before[:2]);self.assertEqual(host.fixed_context(),before[2])
  for value in (2,7,'4'):
   with self.assertRaises(ValueError):host.fixed_context(value)
  self.assertEqual((collector.SOURCE,collector.DESTINATION,host.CONTEXT,host.ASSETS),before)
 def test_native_failure_restores_all_export3_primitives(self):
  before=(native.base.EXPORT,native.base.RECEIPT,native.base.RUN,native.base.verify_command,native.base.save,native.stream.RUN)
  def fail(raw):
   self.assertEqual(native.base.EXPORT,native.EXPORT);self.assertEqual(native.base.RUN,native.RUN)
   self.assertEqual(native.stream.RUN,native.RUN);self.assertEqual(native.base.RECEIPT,native.RECEIPT)
   raise ValueError('explicit fixture failure before any write')
  with patch.object(native.base,'stage',side_effect=fail):
   with self.assertRaisesRegex(ValueError,'fixture failure'):native.stage(b'bounded fixture')
  self.assertEqual((native.base.EXPORT,native.base.RECEIPT,native.base.RUN,native.base.verify_command,native.base.save,native.stream.RUN),before)
 def test_host_export4_requires_its_own_transfer_and_signed_receipt(self):
  sha=lambda data:hashlib.sha256(data).hexdigest()
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);context=root/'.local/phase2/mvp-package-export-4';assets=context/'assets';assets.mkdir(parents=True,mode=0o700)
   context.chmod(0o700);assets.chmod(0o700)
   config=root/'config/phase2';config.mkdir(parents=True)
   (config/'archive-public-trust.json').write_bytes((ROOT/'config/phase2/archive-public-trust.json').read_bytes())
   data={'archive-export.json':b'{}','Release':b'public fixture Release\n','archive-keyring.gpg':(ROOT/'config/phase2/archive-public-key.gpg').read_bytes(),
       'Release.gpg':b'synthetic fixture signature','InRelease':b'synthetic signed fixture'}
   for name,body in data.items():(assets/name).write_bytes(body);(assets/name).chmod(0o644)
   verified={'state':'verified-unsigned-export-transfer','source':'/mnt/lfs/sources/stage/toddy-package-export-4','signed':False,'published':False,
       'archive_export_sha256':sha(data['archive-export.json']),'files':{name:{'sha256':sha(body),'bytes':len(body)} for name,body in data.items() if name not in native.base.LIMITS}}
   (context/'verified.json').write_text(json.dumps(verified));(context/'verified.json').chmod(0o600)
   signed={'state':'signed-publicly-verified-export4','signatures':{name:sha(data[name]) for name in native.base.LIMITS},'published':False}
   (context/'signed.json').write_text(json.dumps(signed));(context/'signed.json').chmod(0o600)
   with patch.object(host,'ROOT',root),patch.object(host,'verify_public') as verification:
    packet=host.packet(4);native.base.decode_packet(packet);verification.assert_called_once()
    signed['state']='signed-publicly-verified-export3';(context/'signed.json').write_text(json.dumps(signed));(context/'signed.json').chmod(0o600)
    with self.assertRaisesRegex(ValueError,'signed3 receipt'):host.packet(4)
