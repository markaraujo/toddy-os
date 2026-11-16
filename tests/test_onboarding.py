"""Private binding lifecycle with synthetic service/keyring/model bytes only."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runtime.setup.pending import PendingStore,Catalog,SetupError
from runtime.setup.onboarding import Onboarding,ConnectionFiles,verify_model,LocalModel

ROOT=Path(__file__).resolve().parents[1]


class Broker:
    def __init__(self,events):
        self.events=events;self.config=__import__('json').loads((ROOT/'config/phase2/profile/config.json').read_text())
        self.revision='a'*64;self.fail_validate=False;self.lost=False
    def selected(self):return self.read('toddy-default')
    def read(self,profile):return {'config':copy.deepcopy(self.config),'profile_revision':self.revision}
    def validate(self,profile,revision,config):
        self.events.append('validate')
        if self.fail_validate:raise ValueError('invalid')
        self.next=config;return 'token'
    def apply(self,*args):
        self.events.append('apply');self.config=self.next;self.revision='b'*64
        if self.lost:raise OSError('lost after apply')
        return {'applied':True}


class Protected:
    def __init__(self,events):self.events=events
    def save(self,*args):self.events.append('save-secret')
    def remove(self,*args):self.events.append('remove-secret')


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.store=PendingStore(self.root/'setup',Catalog((ROOT/'config/phase2/software-catalog.json').read_bytes()));self.addCleanup(self.store.close)
        self.events=[];self.broker=Broker(self.events)
        self.files=ConnectionFiles(self.root/'connections')
        self.api=Onboarding(self.store,connections=self.files,protected=Protected(self.events),broker=self.broker)
        self.settings={'version':1,'adapter_id':'openai','model_id':'synthetic-model','base_url':'https://example.invalid/v1','context_tokens':4096,'max_output_tokens':1024}
    def test_explicit_consent_and_credential_precede_profile_apply(self):
        with self.assertRaisesRegex(SetupError,'consent'):self.api.bind('remote',self.settings,credential='synthetic')
        self.assertEqual(self.events,[])
        result=self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
        self.assertEqual(self.events,['save-secret','validate','apply'])
        self.assertEqual(result['state'],'configured');self.assertFalse(result['provider_contacted'])
        self.assertFalse(self.broker.config['provider']['allow_remote_fallback'])
        data=(self.root/'setup/onboarding.json').read_text()
        self.assertNotIn('synthetic',data);self.assertNotIn('base_url',data)
    def test_selection_revision_change_refuses_before_secret_or_connection(self):
        with self.assertRaisesRegex(SetupError,'profile_changed'):
            self.api.bind('remote',self.settings,credential='synthetic',accepted=True,expected_profile='toddy-default',expected_revision='f'*64)
        self.assertEqual(self.events,[]);self.assertFalse((self.root/'connections').exists())

    def test_definite_pre_apply_failure_restores_new_binding(self):
        self.broker.fail_validate=True
        with self.assertRaisesRegex(SetupError,'binding_failed'):self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
        self.assertEqual(self.events,['save-secret','validate','remove-secret'])
        self.assertEqual(list((self.root/'connections').iterdir()),[])
        self.assertEqual(self.broker.config['provider']['mode'],'deferred')
        self.assertEqual(self.api.state.read()['state'],'failed')
    def test_lost_apply_keeps_binding_reconciles_and_never_replays(self):
        self.broker.lost=True
        result=self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
        self.assertEqual(result['state'],'unknown')
        with self.assertRaisesRegex(SetupError,'reconciliation'):self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
        self.assertEqual(self.api.reconcile()['state'],'configured')
        self.assertEqual(self.events.count('apply'),1)
        self.assertTrue((self.root/'connections'/(result['reference']+'.json')).exists())
        with self.assertRaisesRegex(SetupError,'in_use'):self.api.cleanup()
    def test_secret_save_unknown_never_applies_and_requires_explicit_cleanup(self):
        def failed(*args):raise TimeoutError('possibly committed')
        self.api.protected.save=failed
        with self.assertRaisesRegex(SetupError,'binding_failed'):self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
        self.assertEqual(self.events,[]);self.assertEqual(self.api.state.read()['state'],'cleanup_required')
        self.assertEqual(self.api.cleanup()['state'],'cleaned');self.assertEqual(self.events,['remove-secret'])
    def test_external_connection_drift_refuses_cleanup(self):
        result=self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
        self.broker.config['provider']['connection_ref']=None
        (self.root/'connections'/(result['reference']+'.json')).write_text('owner changed')
        with self.assertRaisesRegex(SetupError,'drift'):self.api.cleanup()
    def test_file_lock_serializes_other_onboarding_instances(self):
        with self.api.state.exclusive():
            with self.assertRaisesRegex(SetupError,'busy'):self.api.bind('remote',self.settings,credential='synthetic',accepted=True)
    def test_local_model_exact_private_bytes_and_hash(self):
        path=self.root/'fixture.gguf';path.write_bytes(b'synthetic model');path.chmod(0o600)
        contract={'model':{'bytes':15,'sha256':hashlib.sha256(b'synthetic model').hexdigest()}}
        with patch('runtime.setup.onboarding.model_contract',return_value=contract):
            self.assertEqual(verify_model(path)['model_path'],str(path))
            path.write_bytes(b'corrupted model')
            with self.assertRaisesRegex(SetupError,'integrity'):verify_model(path)
    def test_endpoint_credentials_and_plaintext_are_refused_before_effects(self):
        for endpoint in ('http://example.invalid/v1','https://user:password@example.invalid/v1'):
            with self.assertRaisesRegex(SetupError,'endpoint'):self.api.bind('remote',{**self.settings,'base_url':endpoint},credential='synthetic',accepted=True)
        self.assertEqual(self.events,[])


class ModelConsentTests(unittest.TestCase):
    def test_exact_license_and_network_consent_before_download(self):
        local=LocalModel('/source-fixture-only')
        review={'state':'acquisition_consent_required','model':{'sha256':'a'*64,'license':'fixture-license'},'path':'/source-fixture-only/model.gguf'}
        with patch.object(local,'review',return_value=review),patch('runtime.acquisition.download.acquire',return_value={'state':'canceled'}) as acquire:
            with self.assertRaisesRegex(SetupError,'license'):local.download(license_accepted=False,network_approved=True)
            with self.assertRaisesRegex(SetupError,'network'):local.download(license_accepted=True,network_approved=False)
            acquire.assert_not_called()
            self.assertEqual(local.download(license_accepted=True,network_approved=True)['state'],'canceled')
            self.assertEqual(acquire.call_args.kwargs['consent'],{'sha256':'a'*64,'license':'fixture-license','network_approved':True})
    def test_already_verified_weights_never_require_or_use_network(self):
        local=LocalModel('/source-fixture-only')
        with patch.object(local,'review',return_value={'state':'verified_existing','model':{'license':'fixture'},'path':'/source-fixture-only/model.gguf'}),patch('runtime.acquisition.download.acquire',side_effect=AssertionError('No network or duplicate download')):
            value=local.download(license_accepted=True,network_approved=False)
            self.assertFalse(value['network_used'])
