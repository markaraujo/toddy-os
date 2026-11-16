"""Qualification driver safety/publication refusal; no native driver is executed."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runtime.setup.pending import SetupError
from tests.test_native_acquisition import fixture

ROOT=Path(__file__).resolve().parents[1]


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/qualification'/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


class NativeQualificationSafetyTests(unittest.TestCase):
    def test_component_driver_cannot_operate_ordinary_development_host(self):
        driver=module('native_acquisition_component')
        if os.getuid()!=0:
            with self.assertRaises(AssertionError):driver.target()
        with patch.object(driver.os,'getuid',return_value=0),patch.object(driver.os,'geteuid',return_value=0), \
                patch.object(driver,'installed_toddy',side_effect=SetupError('native_os_unsupported')), \
                patch.object(driver.subprocess,'check_output',side_effect=AssertionError('No VM/package command')):
            with self.assertRaisesRegex(SetupError,'native_os_unsupported'):driver.target()

    def test_final_publisher_refuses_component_only_even_with_valid_source_shape(self):
        # Stub signing/read APIs intentionally: validates gating, not actual crypto.
        _,_,_,load=fixture('agent-local',level='native-components')
        catalog=load();guard=module('native_acquisition_release_guard')
        with tempfile.TemporaryDirectory() as temporary,patch.object(guard,'private_metadata',return_value=b'{"fingerprint":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","keyring_sha256":"'+b'b'*64+b'"}'), \
                patch.object(guard.NativeCatalog,'load',return_value=catalog):
            with self.assertRaisesRegex(SetupError,'release_full_flow_required'):
                guard.check(Path(temporary),'b'*64,'A'*40)

    def test_final_publisher_requires_independently_pinned_trust_identity(self):
        guard=module('native_acquisition_release_guard')
        with tempfile.TemporaryDirectory() as temporary,patch.object(guard,'private_metadata',return_value=b'{"fingerprint":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","keyring_sha256":"'+b'b'*64+b'"}'):
            with self.assertRaisesRegex(SetupError,'publication_trust_changed'):
                guard.check(Path(temporary),'c'*64,'A'*40)

    def test_no_signed_qualification_is_minted_from_missing_component_results(self):
        driver=module('native_acquisition_component')
        with tempfile.TemporaryDirectory() as temporary,patch.object(driver,'CONTEXT',Path(temporary)),patch.object(driver,'read',side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):driver.report(None,None)
            self.assertFalse((Path(temporary)/'component-qualification.json').exists())
