"""Refusal-only report assembler tests; no actual cases/v2/signatures fabricated."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from runtime.setup.pending import SetupError
from tests.test_native_acquisition_qualification import module


class FullFlowRefusalTests(unittest.TestCase):
    def setUp(self):
        self.driver=module('native_acquisition_full_flow')
        self.release={'packages':[{'name':'toddy-agent','version':'1.0-1'}],'postconditions':{}}
    def test_component_report_cannot_be_used_as_full_case(self):
        component={'qualification_level':'native-components','checks':{'absent_agent_native_backend':True}}
        with patch.object(self.driver,'read',return_value=component):
            with self.assertRaisesRegex(SetupError,'full_case_schema'):self.driver.load_case('install',{},12345)
    def test_missing_actual_case_is_not_assembled(self):
        catalog=SimpleNamespace(releases={'agent-backend':self.release},levels={'agent-backend':'native-components'})
        with patch.object(self.driver,'guard',return_value={'owner_uid':12345}),patch.object(self.driver.NativeCatalog,'load',return_value=catalog),patch.object(self.driver,'bindings',return_value={}),patch.object(self.driver,'load_case',side_effect=FileNotFoundError),patch.object(self.driver,'lifecycle_artifact',side_effect=AssertionError('No lifecycle/report without real cases')):
            with self.assertRaises(FileNotFoundError):self.driver.assemble('agent-backend')
    def test_bare_verified_flag_does_not_satisfy_lifecycle(self):
        case={'bindings':{'code_pins':{}},'observations':{'execution':{'verified':True},'postconditions':{'verified':True}}}
        with self.assertRaisesRegex(SetupError,'actual_package_lifecycle'):self.driver.validate_case('lifecycle',case,12345,self.release)
    def test_empty_no_effect_observations_do_not_satisfy_stop_or_offline(self):
        case={'bindings':{'code_pins':{}},'observations':{'execution':{},'postconditions':{}}}
        for name in ('stop','offline','reconnect','tamper'):
            with self.assertRaises(SetupError):self.driver.validate_case(name,case,12345,self.release)
    def test_actual_signed_second_archive_is_mandatory(self):
        with patch.object(self.driver,'read',side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):self.driver.lifecycle_artifact(self.release,{},None)
    def test_unsupported_action_or_rename_cannot_add_a_check(self):
        with self.assertRaisesRegex(SetupError,'unknown_full_case'):self.driver.validate_case('component-to-full',{},12345,self.release)
    def test_ordinary_development_host_refused_before_receipt_read(self):
        with patch.object(self.driver.os,'getuid',return_value=0),patch.object(self.driver.os,'geteuid',return_value=0),patch.object(self.driver,'installed_toddy',side_effect=SetupError('native_os_unsupported')),patch.object(self.driver,'read',side_effect=AssertionError('No metadata authority on foreign host')):
            with self.assertRaisesRegex(SetupError,'native_os_unsupported'):self.driver.guard()
