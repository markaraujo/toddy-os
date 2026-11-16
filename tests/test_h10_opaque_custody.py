"""Opaque historical-tar custody fixtures; no VM or destructive real-cache use."""
import copy
import gzip
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/host'),str(ROOT/'scripts/build/phase2')]
import phase2_h10_selected_tar_custody as host
import h10_selected_tar_custody as guest


class OpaqueCustodyTests(unittest.TestCase):
    def test_complete_stream_roundtrip_is_private_deterministic_and_never_extracts(self):
        # Opaque bytes may describe setuid files/symlinks; nothing interprets them.
        data=(b'./usr/bin/root-tool\x00mode=4755\x00target=/outside\x00'*10000)+bytes(range(256))
        expected={'bytes':len(data),'sha256':host.hashlib.sha256(data).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);first=root/'one.gz';second=root/'two.gz'
            self.assertEqual(host.stream_compress(io.BytesIO(data),first,len(data)),expected)
            host.stream_compress(io.BytesIO(data),second,len(data))
            self.assertEqual(first.read_bytes(),second.read_bytes())
            self.assertEqual(first.stat().st_mode&0o777,0o600)
            self.assertEqual(gzip.decompress(first.read_bytes()),data)
            proof=host.verify_decompression(first,expected)
            self.assertEqual(proof['state'],'complete-decompression-verified')
            self.assertEqual({x.name for x in root.iterdir()},{'one.gz','two.gz'})

    def test_truncated_oversized_corrupt_or_wrong_digest_never_yields_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for index,data in enumerate((b'short',b'longer-than-five')):
                with self.assertRaises(ValueError):host.stream_compress(io.BytesIO(data),root/str(index),10)
            archive=root/'valid.gz';expected=host.stream_compress(io.BytesIO(b'fixture'),archive,7)
            with self.assertRaises(ValueError):host.verify_decompression(archive,{**expected,'sha256':'a'*64})
            archive.write_bytes(archive.read_bytes()[:-4])
            with self.assertRaises((EOFError,OSError)):host.verify_decompression(archive,expected)

    def test_retirement_requires_complete_proof_before_any_unlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact=Path(temporary)/'selected-root.tar';artifact.write_bytes(b'fixture')
            with patch.object(guest,'ARTIFACT',artifact),patch.object(guest,'read_receipt',return_value={}):
                for proof in ({},{'version':True},None):
                    with self.assertRaises(ValueError):guest.retire(proof)
                    self.assertTrue(artifact.exists())

    def test_only_fixed_file_unlinked_after_durable_intent_all_evidence_remains(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);artifact=root/'selected-root.tar';artifact.write_bytes(b'fixture')
            retained=root/'report.json';retained.write_text('retained evidence')
            before={'.':{'fixture':'directory'},'copy/selected-root.tar':{'fixture':'tar'},'copy/report.json':{'fixture':'evidence'}}
            state={'state':'exported','boot_id':'fixture-boot','producer_sha256':'d'*64,'sha256':'a'*64,'evidence_before':before,'profile':'h10','profile_source_sha256':'d'*64}
            proof={'version':1,'state':'complete-decompression-verified','bytes':guest.SIZE,'sha256':'a'*64,
                'compressed_sha256':'b'*64,'compressed_bytes':100,'host_receipt_sha256':'c'*64,'profile':'h10'}
            saved=[]
            def save(value):
                saved.append(copy.deepcopy(value))
                if value['state']=='retire-intended':self.assertTrue(artifact.exists())
            after={key:value for key,value in before.items() if key!='copy/selected-root.tar'}
            with patch.object(guest,'ARTIFACT',artifact),patch.object(guest,'read_receipt',return_value=state),patch.object(guest,'boot_id',return_value='fixture-boot'),patch.object(guest,'digest',return_value='d'*64),patch.object(guest,'verify',return_value='a'*64),patch.object(guest,'snapshot',return_value=before),patch.object(guest,'snapshot_after_retirement',return_value=after),patch.object(guest,'no_consumers'),patch.object(guest,'save',side_effect=save),patch.object(guest,'free',side_effect=[100,200]):
                result=guest.retire(proof)
            self.assertFalse(artifact.exists());self.assertEqual(retained.read_text(),'retained evidence')
            self.assertEqual([x['state'] for x in saved],['retire-intended','complete'])
            self.assertEqual(result['measured_reclaimed_bytes'],100)

    def test_source_change_or_consumer_stops_before_retirement_intent(self):
        state={'state':'exported','boot_id':'fixture-boot','producer_sha256':'d'*64,'sha256':'a'*64,'evidence_before':{'fixture':'expected'},'profile':'h10','profile_source_sha256':'d'*64}
        proof={'version':1,'state':'complete-decompression-verified','bytes':guest.SIZE,'sha256':'a'*64,
            'compressed_sha256':'b'*64,'compressed_bytes':100,'host_receipt_sha256':'c'*64,'profile':'h10'}
        with patch.object(guest,'read_receipt',return_value=state),patch.object(guest,'boot_id',return_value='fixture-boot'),patch.object(guest,'digest',return_value='d'*64),patch.object(guest,'verify',return_value='a'*64),patch.object(guest,'snapshot',return_value={'fixture':'changed'}),patch.object(guest,'save') as save:
            with self.assertRaisesRegex(ValueError,'custody changed'):guest.retire(proof)
            save.assert_not_called()

    def test_host_commands_have_fixed_candidate_ssh_and_no_payload_extraction(self):
        with patch.object(host.candidate,'ssh',return_value=['ssh','-p','2223','root@127.0.0.1']):
            command=host.command('export')
            self.assertEqual(command[-1],'/usr/bin/python3 /opt/toddy-build/scripts/build/phase2/h10_selected_tar_custody.py export')
            self.assertIn('ServerAliveInterval=15',command)
            with self.assertRaises(ValueError):host.command('delete-any-path')


if __name__=='__main__':unittest.main()
