"""Backing protection checks only; no VM, package or candidate acceptance."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/host'))
spec=importlib.util.spec_from_file_location('candidate_vm',ROOT/'scripts/host/phase2_candidate_vm.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class CandidateGuardTests(unittest.TestCase):
    def test_changed_or_redirected_accepted_base_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);vmroot=root/'vm';base=vmroot/'phase2';base.mkdir(parents=True)
            rows={}
            for name in ('builder.qcow2','lfs-target.qcow2'):
                p=base/name;p.write_bytes(b'fixture image identity only');rows[name]=c.identity(p)
            (root/'docs/evidence').mkdir(parents=True)
            (root/'docs/evidence/B02-completion-stop.json').write_text(json.dumps({'cold_disks':rows}))
            with patch.object(c,'ROOT',root),patch.object(c.vm,'VM',vmroot):
                self.assertEqual(c.bases(),rows)
                p=base/'lfs-target.qcow2';p.write_bytes(b'changed input')
                with self.assertRaisesRegex(AssertionError,'Accepted B02 backing changed'):c.bases()
                p.unlink();p.symlink_to(base/'builder.qcow2')
                with self.assertRaises(AssertionError):c.bases()

    def test_distinct_candidate_and_short_scratch_identity(self):
        self.assertNotEqual(c.WORK,c.phase2_vm.WORK)
        self.assertEqual(c.WORK.parent,c.vm.VM)
        self.assertLessEqual(len('TODDY-QT-RASTER-1'.encode()),20)
        self.assertGreaterEqual(c.RESERVE,100*1024**3+512*1024**2)


if __name__=='__main__':unittest.main()
