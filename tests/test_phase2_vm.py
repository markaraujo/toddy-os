"""Fail closed before starting writable guest disks."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/host'))
spec = importlib.util.spec_from_file_location('phase2_vm', ROOT / 'scripts/host/phase2_vm.py')
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)


class Phase2Guards(unittest.TestCase):
    def test_historical_start_restore_guard_preserves_active_clone_backing(self):
        with patch.object(vm.vm, 'run', return_value=subprocess.CompletedProcess([], 0, 'toddy-phase2\n')):
            with self.assertRaisesRegex(SystemExit, 'preserve its cold foundation'):
                vm.vm.require_phase2_inactive()

    def test_historical_guard_does_not_hide_docker_failure(self):
        with patch.object(vm.vm, 'run', side_effect=subprocess.CalledProcessError(1, ['docker'])):
            with self.assertRaises(subprocess.CalledProcessError):
                vm.vm.require_phase2_inactive()

    def test_another_project_vm_prevents_prepare_or_start(self):
        with patch.object(vm, 'run', return_value=subprocess.CompletedProcess([], 0, 'toddy-builder\n')):
            with self.assertRaisesRegex(SystemExit, 'Stop project VMs'):
                vm.require_quiescent()

    def test_docker_failure_is_not_quiescence(self):
        with patch.object(vm, 'run', side_effect=subprocess.CalledProcessError(1, ['docker'])):
            with self.assertRaises(subprocess.CalledProcessError):
                vm.require_quiescent()

    def test_changed_backing_refuses_start_before_docker_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / 'phase2'
            work.mkdir()
            (root / 'approval.md').write_text('Fixture approval only')
            (root / 'status.json').write_text(json.dumps({'owner_review': {
                'phase_2_approved': True, 'approval_evidence': 'approval.md'}}))
            disk = root / 'lfs-target.qcow2'
            disk.write_bytes(b'original')
            receipt = {'disks': {'lfs-target.qcow2': {'identity': vm.backing_identity(disk)}}}
            (work / 'backing.json').write_text(json.dumps(receipt))
            disk.write_bytes(b'changed bytes')
            with patch.object(vm, 'ROOT', root), patch.object(vm, 'WORK', work), \
                 patch.object(vm.vm, 'VM', root), patch.object(vm, 'require_quiescent'), \
                 patch.object(sys, 'argv', ['phase2_vm.py', 'start']), patch.object(vm, 'run') as run:
                with self.assertRaisesRegex(SystemExit, 'Backing identity changed'):
                    vm.main()
                run.assert_not_called()

    def test_missing_approval_refuses_guest_access(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / 'phase2'
            (root / 'status.json').write_text(json.dumps({'owner_review': {'phase_2_approved': False}}))
            with patch.object(vm, 'ROOT', root), patch.object(vm, 'WORK', work), \
                 patch.object(vm.vm, 'VM', root), patch.object(vm, 'run') as run, \
                 patch.object(sys, 'argv', ['phase2_vm.py', 'start']):
                with self.assertRaisesRegex(SystemExit, 'approval required'):
                    vm.main()
                run.assert_not_called()
