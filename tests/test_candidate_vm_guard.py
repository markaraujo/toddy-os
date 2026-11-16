"""Backing protection checks only; no VM, package or candidate acceptance."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/host'))
spec=importlib.util.spec_from_file_location('candidate_vm',ROOT/'scripts/host/phase2_candidate_vm.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class CandidateGuardTests(unittest.TestCase):
    def test_root_ssh_requires_the_candidate_mount_and_port_owner(self):
        row={'Id':'fixture-owned-container','Name':'/'+c.NAME,'State':{'Running':True},
             'Config':{'Labels':{'toddy.candidate':'phase2-candidate'},'Cmd':[
                 'file=/vm/phase2-candidate/builder.qcow2,if=none','file=/vm/phase2-candidate/lfs-target.qcow2,if=none']},
             'Mounts':[{'Type':'bind','Source':str(c.vm.VM),'Destination':'/vm','RW':False},
                       {'Type':'bind','Source':str(c.WORK),'Destination':'/vm/phase2-candidate','RW':True}],
             'NetworkSettings':{'Ports':{'2223/tcp':[{'HostIp':'127.0.0.1','HostPort':'2223'}]}}}
        def inspected(*args,**kwargs):return subprocess.CompletedProcess(args,0,json.dumps([row]),'')
        with patch.object(c,'run',side_effect=inspected):
            self.assertEqual(c.owned(),'fixture-owned-container')
            row['Mounts'][0]['RW']=True
            with self.assertRaises(AssertionError):c.owned()
            row['Mounts'][0]['RW']=False
            row['Mounts'][1]['Source']=str(c.phase2_vm.WORK)
            with self.assertRaises(KeyError):c.owned()

    def test_changed_or_redirected_accepted_base_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);vmroot=root/'vm';base=vmroot/'phase2';base.mkdir(parents=True)
            foundation={}
            for name in ('builder-base.img','builder.qcow2','lfs-target.qcow2','seed.img'):
                p=vmroot/name;p.write_bytes(b'fixture frozen foundation');foundation[name]={'identity':c.identity(p)}
            (base/'backing.json').write_text(json.dumps({'disks':foundation}))
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
        self.assertEqual(Path('/vm/phase2-candidate').relative_to('/vm'),c.WORK.relative_to(c.vm.VM))
        self.assertLessEqual(len('TODDY-QT-RASTER-1'.encode()),20)
        self.assertGreaterEqual(c.RESERVE,100*1024**3+512*1024**2)


if __name__=='__main__':unittest.main()
