"""Refusal-only source fixtures; never execute a CPU denial/native backend run."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from runtime.setup.pending import SetupError
from runtime.setup.runtime_compat import CPU_FLAGS
from tests.test_native_acquisition_qualification import module


class NativeCPUDenialRefusalTests(unittest.TestCase):
    def setUp(self):
        self.driver=module('native_acquisition_component')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.context=Path(self.tmp.name)
        self.patch=patch.object(self.driver,'CONTEXT',self.context);self.patch.start();self.addCleanup(self.patch.stop)
        self.adapter=SimpleNamespace(release={'id':'local-runtime','packages':[{'name':'llama-cpp'}]},review=None,
            ensure_current=lambda:None)
        self.marker={'owner_uid':12345}
    def test_supported_cpu_is_refused_before_backend_or_intent(self):
        with patch('runtime.setup.runtime_compat.cpu_features',return_value=('x86_64',set(CPU_FLAGS))), \
                patch.object(self.driver,'NativeBackend',side_effect=AssertionError('No backend on supported qualification CPU')):
            with self.assertRaisesRegex(SetupError,'actual_unsupported_cpu'):self.driver.cpu_denial(self.adapter,self.marker)
        self.assertEqual(list(self.context.iterdir()),[])
    def test_nonlocal_signed_candidate_cannot_be_used(self):
        self.adapter.release={'id':'agent-backend','packages':[{'name':'toddy-agent'}]}
        with patch('runtime.setup.runtime_compat.cpu_features',side_effect=AssertionError('No hardware read for wrong release')):
            with self.assertRaisesRegex(SetupError,'local_candidate'):self.driver.cpu_denial(self.adapter,self.marker)
        self.assertEqual(list(self.context.iterdir()),[])
    def test_existing_uncertain_intent_is_not_replayed(self):
        (self.context/'cpu-denial-intent.json').write_text('preserve unknown original effect')
        with patch('runtime.setup.runtime_compat.cpu_features',side_effect=AssertionError('No replay')):
            with self.assertRaisesRegex(SetupError,'existing_cpu'):self.driver.cpu_denial(self.adapter,self.marker)
        self.assertEqual((self.context/'cpu-denial-intent.json').read_text(),'preserve unknown original effect')
    def test_fabricated_supported_review_on_unsupported_cpu_refused(self):
        self.adapter.review={'runtime_compatible':True}
        with patch('runtime.setup.runtime_compat.cpu_features',return_value=('x86_64',set(CPU_FLAGS)-{'avx2'})), \
                patch.object(self.driver,'NativeBackend',side_effect=AssertionError('No supported review bypass')):
            with self.assertRaisesRegex(SetupError,'unsupported_review_forbidden'):self.driver.cpu_denial(self.adapter,self.marker)
        self.assertEqual(list(self.context.iterdir()),[])
    def test_bare_previous_cpu_marker_cannot_satisfy_component_report(self):
        self.adapter.code={};self.adapter.trust={}
        with self.assertRaisesRegex(SetupError,'actual_masked_cpu_receipt'):
            self.driver.validate_cpu_receipt({'native_result':'denied_before_apt','code_pins':{},'trust_pins':{}},self.adapter)
    def test_existing_profiler_refused_without_observing_or_replacing_runner(self):
        with patch('runtime.setup.runtime_compat.cpu_features',return_value=('x86_64',set(CPU_FLAGS)-{'avx2'})), \
                patch.object(self.driver,'active',return_value=None),patch.object(self.driver.sys,'getprofile',return_value=object()), \
                patch.object(self.driver,'acquisition_snapshot',side_effect=AssertionError('No state read before observer custody')):
            with self.assertRaisesRegex(SetupError,'unmodified_native_observer'):self.driver.cpu_denial(self.adapter,self.marker)
        self.assertEqual(list(self.context.iterdir()),[])
