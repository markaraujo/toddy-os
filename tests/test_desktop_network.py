"""Exercise real systemd conditions for mutually exclusive staged ownership."""
from pathlib import Path
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('desktop_network',ROOT/'scripts/build/phase2/desktop_network.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class DesktopNetworkTests(unittest.TestCase):
    def test_real_conditions_select_exactly_one_owner(self):
        tool=shutil.which('systemd-analyze')
        if not tool:self.skipTest('Actual systemd condition evaluator unavailable')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);stage=root/'stage';conffiles=module.stage(stage,ROOT)
            marker=stage/module.MARKER.lstrip('/')
            unit_paths=[stage/n.lstrip('/') for n in conffiles if n.endswith('owner.conf')]
            for present in [True,False]:
                if not present:marker.unlink()
                outcomes=[]
                for path in unit_paths:
                    condition=next(l for l in path.read_text().splitlines() if l.startswith('ConditionPathExists='))
                    condition=condition.replace(module.MARKER,str(marker))
                    result=subprocess.run([tool,'condition',condition],capture_output=True,text=True)
                    self.assertIn(result.returncode,[0,1],result.stderr)
                    outcomes.append(result.returncode==0)
                self.assertEqual(outcomes,[present,not present])

    def test_payload_enables_only_daemon_and_preserves_existing_stages(self):
        with tempfile.TemporaryDirectory() as d:
            stage=Path(d)/'stage';module.stage(stage,ROOT)
            link=stage/'etc/systemd/system/multi-user.target.wants/NetworkManager.service'
            self.assertEqual(os.readlink(link),'/usr/lib/systemd/system/NetworkManager.service')
            self.assertEqual([p.name for p in link.parent.iterdir()],['NetworkManager.service'])
            self.assertNotIn('system-connections',{p.name for p in stage.rglob('*')})
            original=(stage/module.MARKER.lstrip('/')).read_bytes()
            with self.assertRaises(AssertionError):module.stage(stage,ROOT)
            self.assertEqual((stage/module.MARKER.lstrip('/')).read_bytes(),original)

    def test_redirected_stage_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'stage';p.symlink_to(Path(d)/'missing')
            with self.assertRaises(AssertionError):module.stage(p,ROOT)
