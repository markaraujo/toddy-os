"""Protect accepted build evidence from the observed preparer variable-shadow bug."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('worker_receipt_guard',Path(__file__).resolve().parents[1]/'scripts/build/phase2/worker_receipt_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)

class WorkerReceiptGuardTests(unittest.TestCase):
 def test_acceptance_record_cannot_be_overwritten(self):
  with self.assertRaises(ValueError):guard.validate(Path('/var/log/toddy/build/b02-libgtop-install.success.json'),'mitkrb')
 def test_another_workers_record_cannot_be_overwritten(self):
  with self.assertRaises(ValueError):guard.validate(Path('/var/log/toddy/phase2/libgtop-shared-scratch-1.json'),'mitkrb')
 def test_traversal_and_unknown_owner_cannot_escape(self):
  with self.assertRaises(ValueError):guard.validate(Path('/var/log/toddy/phase2/../build/mitkrb-shared-scratch-1.json'),'mitkrb')
  with self.assertRaises(ValueError):guard.validate(Path('/var/log/toddy/phase2/unknown-shared-scratch-1.json'),'unknown')
 def test_only_own_receipt_is_allowed(self):
  for component in ['cups-layout','cups','mitkrb','libgtop','modemmanager']:
   guard.validate(Path('/var/log/toddy/phase2')/(component+'-shared-scratch-1.json'),component)
