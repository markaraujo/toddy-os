"""Second literal profile isolation; shared opaque compression, no VM activity."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/host'),str(ROOT/'scripts/build/phase2')]
import opaque_tar_profiles as profiles
import h10_selected_tar_custody as guest
import phase2_h10_selected_tar_custody as host


class H11ProfileTests(unittest.TestCase):
    def tearDown(self):
        guest.configure('h10');host.configure('h10')

    def test_second_literal_profile_has_measured_independent_identity_and_receipts(self):
        h10=profiles.profile('h10');h11=profiles.profile('h11')
        self.assertEqual(h11['bytes'],3731630080)
        self.assertEqual(h11['allocated_bytes'],3731636224)
        self.assertEqual(h11['inode'],1239398)
        self.assertEqual(h11['evidence_inode'],1239390)
        self.assertEqual(h11['copy_inode'],1239393)
        self.assertEqual(h11['entries'],31)
        self.assertEqual(h11['manifest'],'20-image-manifest.json')
        self.assertNotEqual(h10['sha256'],h11['sha256'])
        old_receipt=guest.RECEIPT;old_context=host.CONTEXT
        guest.configure('h11');host.configure('h11')
        self.assertEqual(guest.RECEIPT.name,'h11-selected-tar-custody-1.json')
        self.assertEqual(host.CONTEXT.name,'h11-selected-tar-custody-1')
        self.assertNotEqual(old_receipt,guest.RECEIPT);self.assertNotEqual(old_context,host.CONTEXT)
        self.assertEqual(guest.ARTIFACT.as_posix(),'/mnt/lfs/sources/stage/h11-release-root-evidence/copy/selected-root.tar')

    def test_profile_selection_never_accepts_arbitrary_paths_and_returns_copies(self):
        for value in ('../h11','h11-release-compression','h12','/tmp/cache'):
            with self.assertRaises(ValueError):profiles.profile(value)
            with self.assertRaises(ValueError):guest.configure(value)
        value=profiles.profile('h11');value['inode']=1
        self.assertEqual(profiles.profile('h11')['inode'],1239398)

    def test_h11_uses_shared_stream_mechanism_with_current_profile_size(self):
        host.configure('h11')
        with tempfile.TemporaryDirectory() as temporary,patch.object(host,'SIZE',7):
            archive=Path(temporary)/'profile.gz'
            proof=host.stream_compress(io.BytesIO(b'fixture'),archive)
            self.assertEqual(proof['bytes'],7)
            self.assertEqual(host.verify_decompression(archive,proof)['sha256'],proof['sha256'])
        with patch.object(host.candidate,'ssh',return_value=['ssh','-p','2223','root@127.0.0.1']):
            self.assertEqual(host.command('export')[-1],'/usr/bin/python3 /opt/toddy-build/scripts/build/phase2/h10_selected_tar_custody.py h11 export')

    def test_h10_proof_cannot_authorize_h11_retirement(self):
        guest.configure('h11')
        proof={'version':1,'profile':'h10','state':'complete-decompression-verified','bytes':guest.SIZE,
            'sha256':'a'*64,'compressed_sha256':'b'*64,'compressed_bytes':1,'host_receipt_sha256':'c'*64}
        with patch.object(guest,'read_receipt',return_value={}),patch.object(guest,'verify') as verify,patch.object(guest,'save') as save:
            with self.assertRaisesRegex(ValueError,'proof required'):guest.retire(proof)
            verify.assert_not_called();save.assert_not_called()


if __name__=='__main__':unittest.main()
