"""Exercise actual byte restoration/refusal and Linux cross-process image locks."""
import errno
import gzip
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cold_custody',ROOT/'scripts/host/phase2_compress_cold_checkpoints.py')
custody=importlib.util.module_from_spec(spec);spec.loader.exec_module(custody)


class ColdCheckpointCustody(unittest.TestCase):
    def test_full_roundtrip_and_wrong_digest_refusal(self):
        raw=b'\0'*16000+bytes(range(256))*200
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'fixture.qcow2.gz';p.write_bytes(gzip.compress(raw,mtime=0))
            proof=custody.verify_gzip(p,hashlib.sha256(raw).hexdigest(),len(raw))
            self.assertEqual(proof['restored_bytes'],len(raw))
            with self.assertRaises(AssertionError):custody.verify_gzip(p,'0'*64,len(raw))
            damaged=bytearray(p.read_bytes());damaged[-8]^=1;p.write_bytes(damaged)
            with self.assertRaises((gzip.BadGzipFile,EOFError)):custody.verify_gzip(p,hashlib.sha256(raw).hexdigest(),len(raw))

    def test_held_full_image_lock_blocks_another_process(self):
        with tempfile.TemporaryFile() as f:
            custody.exclusive(f.fileno())
            script='''import errno,fcntl,os,struct,sys
try:fcntl.fcntl(int(sys.argv[1]),fcntl.F_OFD_SETLK,struct.pack('hhqqi4x',fcntl.F_RDLCK,os.SEEK_SET,0,0,0))
except OSError as error:sys.exit(0 if error.errno in (errno.EAGAIN,errno.EACCES) else 2)
sys.exit(1)
'''
            # Cross-process reopen via proc avoids inheriting the locked description.
            script=script.replace('int(sys.argv[1])',"os.open(sys.argv[1],os.O_RDONLY)")
            result=subprocess.run([sys.executable,'-c',script,f'/proc/{os.getpid()}/fd/{f.fileno()}'],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
