"""Tiny own-deb/ephemeral-signature fixtures; no product or host installation.

Fake runner records Dpkg installation argv and only extracts test archives into
private temporary directories. Finalizer receipts are explicitly synthetic.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('offline_payload', ROOT / 'scripts/build/phase2/offline_payload.py')
payload = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(payload)


def command(arguments, *, output=False):
    return subprocess.run(arguments, check=True, stdout=subprocess.PIPE if output else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, timeout=15).stdout


def snapshot(root):
    result = {}
    for path in sorted(Path(root).rglob('*')):
        metadata = path.lstat()
        row = {'mode': metadata.st_mode, 'uid': metadata.st_uid, 'gid': metadata.st_gid}
        if path.is_dir():
            row['directory'] = True
        elif path.is_symlink():
            row['symlink'] = os.readlink(path)
        else:
            row['sha256'] = payload.digest(path)
        result['/' + path.relative_to(root).as_posix()] = row
    return result


class OfflinePayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if any(not shutil.which(tool) for tool in ('gpg', 'gpgv', 'dpkg-deb', 'dpkg')):
            raise unittest.SkipTest('required host fixture package/signature tools unavailable')
        cls.key_temp = tempfile.TemporaryDirectory()
        cls.key_home = Path(cls.key_temp.name) / 'fixture-gnupg'
        cls.key_home.mkdir(mode=0o700)
        command(['gpg', '--homedir', str(cls.key_home), '--no-options', '--batch', '--pinentry-mode',
            'loopback', '--passphrase', '', '--quick-generate-key',
            'Toddy ephemeral fixture <fixture@example.invalid>', 'ed25519', 'sign', '0'])
        cls.public = command(['gpg', '--homedir', str(cls.key_home), '--no-options', '--batch', '--export'], output=True)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['gpgconf', '--homedir', str(cls.key_home), '--kill', 'gpg-agent'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        cls.key_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.records = self.root / 'records'
        self.cache = self.root / 'cache'
        self.records.mkdir()
        self.cache.mkdir()
        self.components = []
        for name, depends in [('fixture-base', ''), ('toddy-branding', 'fixture-base (>= 1.0)'),
                              ('toddy-assistant', 'fixture-base (= 1.0), toddy-branding')]:
            self.components.append(self.package(name, depends=depends))
        self.profile = self.root / 'profile.json'
        self.profile.write_bytes(payload.encoded({'retained_foundation_packages': ['fixture-base'],
            'desktop_roots': [], 'excluded_product_roots': ['toddy-agent', 'toddy-assistant', 'nodejs']}))
        self.projection = self.root / 'projection.json'
        self.write_projection()
        self.catalog = self.root / 'catalog.json'
        self.catalog.write_bytes(b'{"schema_version":1,"candidates":[],"qualified_releases":[]}\n')
        self.keyring = self.root / 'trusted-keyring.gpg'
        self.keyring.write_bytes(self.public)
        self.packages = self.root / 'Packages'
        self.release = self.root / 'Release'
        self.signature = self.root / 'Release.gpg'
        self.sign_repository()

    def tearDown(self):
        self.temp.cleanup()

    def package(self, name, *, depends='', extra_control=None, extra_files=None):
        stage = self.root / ('stage-' + name)
        stage.mkdir(mode=0o755)
        stage.chmod(0o755)
        doc = stage / 'usr/share/doc' / name
        doc.mkdir(parents=True)
        (doc / 'copyright').write_text('Original fixture code: MIT. No native/product acceptance.\n')
        if name == 'fixture-base':
            (stage / 'var').mkdir()
        for relative, data in (extra_files or {}).items():
            path = stage / relative.lstrip('/')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for directory in [stage, *(path for path in stage.rglob('*') if path.is_dir())]:
            directory.chmod(0o755)
        expected = snapshot(stage)
        for row in expected.values():
            row['uid'] = 0
            row['gid'] = 0
        control = stage / 'DEBIAN'
        control.mkdir()
        fields = f'Package: {name}\nVersion: 1.0\nArchitecture: all\nMaintainer: Fixture <fixture@example.invalid>\nDescription: source-only fixture\n'
        if depends:
            fields += 'Depends: ' + depends + '\n'
        (control / 'control').write_text(fields)
        if extra_control:
            (control / extra_control).write_text('#!/bin/sh\nexit 0\n')
            (control / extra_control).chmod(0o755)
        archive = self.cache / (name + '_1.0_all.deb')
        command(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(archive)])
        record = {'name': name, 'version': '1.0', 'installed': True,
            'archive_sha256': payload.digest(archive), 'recipe_sha256': 'a' * 64,
            'sources': [], 'source_kind': 'book-derived-versioned-recipe',
            'payload': expected, 'generated_paths': []}
        record_path = self.records / (name + '_1.0_all.json')
        record_path.write_bytes(payload.encoded(record))
        return {'name': name, 'version': '1.0', 'architecture': 'all', 'depends': depends,
            'archive_sha256': record['archive_sha256'], 'component_record_sha256': payload.digest(record_path),
            'recipe_sha256': record['recipe_sha256'], 'sources': [],
            'copyright': {'path': '/usr/share/doc/' + name + '/copyright',
                'sha256': expected['/usr/share/doc/' + name + '/copyright']['sha256']},
            'source_notices_index': None}

    def write_projection(self):
        self.projection.write_bytes(payload.encoded({'schema_version': 1,
            'profile_sha256': payload.digest(self.profile), 'components': [self.components[0]]}))

    def sign_repository(self):
        rows = []
        for component in self.components:
            leaf = component['name'] + '_1.0_all.deb'
            rows.append('Package: ' + component['name'] + '\nVersion: 1.0\nArchitecture: all\n'
                + 'Filename: pool/' + leaf + '\nSize: ' + str((self.cache / leaf).stat().st_size)
                + '\nSHA256: ' + component['archive_sha256'] + '\n')
        self.packages.write_text('\n'.join(rows))
        self.release.write_text('Origin: Toddy OS\nSHA256:\n ' + payload.digest(self.packages)
            + ' ' + str(self.packages.stat().st_size) + ' main/binary-all/Packages\n')
        command(['gpg', '--homedir', str(self.key_home), '--no-options', '--batch', '--yes', '--pinentry-mode',
            'loopback', '--passphrase', '', '--detach-sign', '--output', str(self.signature), str(self.release)])

    def trust(self):
        return payload.ReleaseTrust(keyring=self.keyring, expected_key_sha256=payload.digest(self.keyring),
            release=self.release, signature=self.signature, packages=self.packages, index_path='main/binary-all/Packages')

    def prepare(self, destination=None, **kwargs):
        arguments = dict(profile_path=self.profile, projection_path=self.projection,
            records_directory=self.records, archive_directory=self.cache, catalog_path=self.catalog,
            destination=destination or self.root / 'bundle', trust=self.trust(),
            generated_bindings={}, additional_components=self.components[1:], required_recovery_paths=())
        arguments.update(kwargs)
        # Tiny ephemeral host fixtures do not claim actual guest free space.
        with patch.object(payload,'available_bytes',return_value=payload.RESERVE_BYTES+1024**3):
            return payload.prepare(**arguments)

    def test_storage_counts_real_hardlinks_once_but_retains_legacy_path_bytes(self):
        stage=self.root/'hardlink-stage';(stage/'usr/share/fixture').mkdir(parents=True)
        source=stage/'usr/share/fixture/a';source.write_bytes(b'x')
        os.link(source,source.with_name('b'));source.with_name('c').write_bytes(b'x')
        (stage/'DEBIAN').mkdir();(stage/'DEBIAN/control').write_text('Package: fixture-links\nVersion: 1\nArchitecture: all\nMaintainer: Fixture <f@example.invalid>\nDescription: source fixture\n')
        archive=self.cache/'links.deb';command(['dpkg-deb','--root-owner-group','--build',str(stage),str(archive)])
        measured={};_,_,legacy=payload.archive_contents(archive,storage=measured)
        report=payload.storage_measurements({'fixture-links':measured},{'fresh_directories':{}},4096)
        self.assertEqual(legacy,3);self.assertEqual(report['logical_regular_path_bytes'],3)
        self.assertEqual(report['unique_regular_bytes'],2);self.assertEqual(report['regular_inodes'],2)
        self.assertEqual(report['hardlink_aliases'],1)
        self.assertGreaterEqual(report['rounded_file_data_bytes'],8192)
        self.assertGreater(report['native_database_staging_bound_bytes'],0)

    def test_complete_bundle_copy_is_bounded_before_destination_creation(self):
        manifest=self.prepare();storage=manifest['storage']
        self.assertEqual(manifest['bytes'],storage['logical_regular_path_bytes'])
        self.assertGreater(storage['root_storage_bound_bytes'],manifest['bytes'])
        self.assertGreater(storage['bundle_copy_bound_bytes'],sum(row['archive_bytes'] for row in manifest['components']))
        destination=self.root/'insufficient-space'
        with patch.object(payload,'require_capacity',side_effect=payload.PayloadError('fixture capacity refusal')):
            with self.assertRaisesRegex(payload.PayloadError,'capacity refusal'):self.prepare(destination)
        self.assertFalse(destination.exists())
        with patch.object(payload,'available_bytes',return_value=payload.RESERVE_BYTES+99):
            with self.assertRaisesRegex(payload.PayloadError,'16gib'):payload.require_capacity(self.root,100)

    def test_real_ephemeral_signature_and_exact_owned_archive_bundle(self):
        first = self.prepare()
        second = self.prepare(self.root / 'second-bundle')
        self.assertEqual(first, second)
        self.assertFalse(first['installed_ready'])
        self.assertEqual({row['name'] for row in first['components']}, {'fixture-base', 'toddy-assistant', 'toddy-branding'})
        self.assertGreater(first['bytes'], 0)
        self.assertEqual(set(first['required_finalizer_checks']), payload.CHECKS)
        self.assertEqual((self.root / 'bundle/repository/trusted-keyring.gpg').read_bytes(), self.public)
        payload.public_key_only(self.public)
        with self.assertRaisesRegex(payload.PayloadError, 'nonpublic_key_packet'):
            payload.public_key_only(b'\xc5\x01\x00')  # synthetic secret-key packet
        self.assertEqual(payload.component_from_record(self.records / 'toddy-assistant_1.0_all.json', self.cache), self.components[2])
        checklist = payload.requirements(self.projection, self.records)
        self.assertFalse(checklist['ready_for_install'])
        self.assertEqual(checklist['additional_required_packages'], ['toddy-assistant', 'toddy-branding'])

    def test_mvp_requires_explicit_profile_and_rechecks_signed_bundle_policy(self):
        for name in sorted(payload.MVP_ROOTS):
            self.components.append(self.package(name))
        self.profile.write_bytes(payload.encoded({'retained_foundation_packages': ['fixture-base'],
            'desktop_roots': sorted(payload.MVP_ROOTS), 'excluded_product_roots': ['toddy-assistant'],
            'delivery_class': payload.MVP_CLASS, 'g2_eligible': False, 'automatic_activation': False}))
        self.projection.write_bytes(payload.encoded({'schema_version': 1,
            'profile_sha256': payload.digest(self.profile),
            'components': [self.components[0], *self.components[3:]]}))
        self.sign_repository()
        manifest = self.prepare(additional_components=self.components[1:3])
        self.assertEqual(manifest['delivery_class'], payload.MVP_CLASS)
        self.assertIs(manifest['g2_eligible'], False)
        prepared = payload.PreparedPayload(self.root/'bundle',
            manifest_sha256=payload.digest(self.root/'bundle/manifest.json'), runner=None, finalizer=None)
        self.assertEqual(prepared._load(), manifest)
        profile = payload.strict(self.profile.read_bytes())
        del profile['delivery_class']
        self.profile.write_bytes(payload.encoded(profile))
        self.projection.write_bytes(payload.encoded({'schema_version': 1,
            'profile_sha256': payload.digest(self.profile), 'components': [self.components[0], *self.components[3:]]}))
        with self.assertRaisesRegex(payload.PayloadError, 'offline_package_set'):
            self.prepare(destination=self.root/'rejected', additional_components=self.components[1:3])

    def test_signature_tamper_and_wrong_reviewed_key_are_denied(self):
        self.release.write_text(self.release.read_text() + 'Suite: tampered\n')
        with self.assertRaisesRegex(payload.PayloadError, 'signature'):
            self.prepare()
        self.assertFalse((self.root / 'bundle').exists())
        trust = self.trust()
        trust.key_hash = '0' * 64
        with self.assertRaisesRegex(payload.PayloadError, 'key_changed'):
            trust.verify([])

    def test_archive_record_or_profile_tampering_is_not_a_valid_component(self):
        archive = self.cache / 'fixture-base_1.0_all.deb'
        with archive.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(payload.PayloadError, 'custody'):
            self.prepare()
        self.profile.write_text(self.profile.read_text() + ' ')
        with self.assertRaisesRegex(payload.PayloadError, 'profile_binding'):
            self.prepare()

    def test_versioned_dependency_does_not_accept_a_matching_name_only(self):
        components = {'dependency': {'version': '1.0', 'depends': ''},
            'consumer': {'version': '1.0', 'depends': 'dependency (>= 2.0)'}}
        with self.assertRaisesRegex(payload.PayloadError, 'unsatisfied_versioned_dependency'):
            payload.dependency_closure(components, {'consumer'})
        components['consumer']['depends'] = 'dependency (>= 1.0)'
        self.assertEqual(payload.dependency_closure(components, {'consumer'}), {'dependency', 'consumer'})

    def test_scripts_triggers_and_dirty_root_payload_are_unqualified(self):
        script = self.package('fixture-script', extra_control='postinst')
        with self.assertRaisesRegex(payload.PayloadError, 'maintainer_scripts'):
            payload.archive_contents(self.cache / 'fixture-script_1.0_all.deb')
        bad = self.package('fixture-personal', extra_files={'/home/owner/.ssh/id_rsa': b'dummy private fixture'})
        record = json.loads((self.records / 'fixture-personal_1.0_all.json').read_text())
        with self.assertRaisesRegex(ValueError, 'Runtime/home/cache/log'):
            payload.inventory([record])

    def test_terminal_private_reference_is_immutable_and_unknown_caches_stay_guarded(self):
        path='/usr/lib/gnome-terminal/gschemas.compiled'
        expected=payload.IMMUTABLE_SCHEMA_REFERENCES[path]
        self.assertFalse(payload.generated_artifact(path))
        entries={path:{'sha256':expected}}
        self.assertEqual(payload.validate_generated([],entries,{})['owned_cache_bindings'],{})
        entries[path]['sha256']='0'*64
        with self.assertRaisesRegex(payload.PayloadError,'immutable_schema_reference_changed'):
            payload.validate_generated([],entries,{})
        for other in ('/usr/share/glib-2.0/schemas/gschemas.compiled','/usr/lib/unknown/gschemas.compiled'):
            self.assertTrue(payload.generated_artifact(other))
            with self.assertRaisesRegex(payload.PayloadError,'inputs_empty'):payload.cache_namespace(other,{})

    def test_cache_requires_exact_selected_inputs_and_tool_provenance(self):
        entries = {'/usr/share/glib-2.0/schemas/gschemas.compiled': {'sha256': 'a' * 64},
            '/usr/share/glib-2.0/schemas/one.gschema.xml': {'sha256': 'b' * 64},
            '/usr/share/glib-2.0/schemas/two.gschema.xml': {'sha256': 'c' * 64},
            '/usr/bin/glib-compile-schemas': {'sha256': 'd' * 64}}
        with self.assertRaisesRegex(payload.PayloadError, 'binding_incomplete'):
            payload.validate_generated([], entries, {})
        path = '/usr/share/glib-2.0/schemas/gschemas.compiled'
        binding = {'output_sha256': 'a' * 64, 'tool': {'path': '/usr/bin/glib-compile-schemas', 'sha256': 'd' * 64},
            'inputs': {'/usr/share/glib-2.0/schemas/one.gschema.xml': 'b' * 64},
            'input_namespace_sha256': hashlib.sha256(payload.encoded(payload.cache_namespace(path, entries))).hexdigest(),
            'native_evidence_sha256': 'e' * 64}
        with self.assertRaisesRegex(payload.PayloadError, 'union_inputs_differ'):
            payload.validate_generated([], entries, {path: binding})
        binding['inputs']['/usr/share/glib-2.0/schemas/two.gschema.xml'] = 'c' * 64
        self.assertEqual(payload.validate_generated([], entries, {path: binding})['owned_cache_bindings'][path], binding)

    def test_required_foundation_recovery_is_never_silently_dropped(self):
        with self.assertRaisesRegex(payload.PayloadError, 'recovery_missing'):
            self.prepare(required_recovery_paths=['/boot/vmlinuz-accepted-recovery'])

    def test_default_target_guard_rejects_unmounted_host_tree_before_dpkg(self):
        self.prepare()
        bundle = self.root / 'bundle'
        adapter = payload.PreparedPayload(bundle, manifest_sha256=payload.digest(bundle / 'manifest.json'),
            runner=None, finalizer=lambda *_: None)
        with self.assertRaisesRegex(payload.PayloadError, 'designated_mounted_target'):
            adapter._target_guard(self.root, {'options': {'operation_id': 'a' * 32}})

    def test_whole_image_audit_rejects_unowned_additions_and_changed_owned_bytes(self):
        target = self.root / 'audit-tree'
        target.mkdir()
        (target / 'known').write_bytes(b'known fixture')
        manifest = {'ownership': {'entries': snapshot(target)}, 'required_recovery_paths': ['/known']}
        self.assertEqual(payload.PreparedPayload.audit_tree(target, manifest, {}), snapshot(target))
        (target / 'secret').write_bytes(b'unknown dummy data')
        with self.assertRaisesRegex(payload.PayloadError, 'whole_image_attribution'):
            payload.PreparedPayload.audit_tree(target, manifest, {})
        (target / 'secret').unlink()
        (target / 'known').write_bytes(b'changed')
        with self.assertRaisesRegex(payload.PayloadError, 'whole_image_attribution'):
            payload.PreparedPayload.audit_tree(target, manifest, {})

    def test_installer_callback_rechecks_trust_and_rejects_incomplete_finalizer(self):
        manifest = self.prepare()
        bundle = self.root / 'bundle'
        manifest_sha = payload.digest(bundle / 'manifest.json')
        plan = {'payload': {'sha256': manifest_sha, 'catalog_sha256': manifest['catalog_sha256'], 'bytes': manifest['bytes']},
                'options': {'operation_id': 'a' * 32}}
        class FakeRunner:
            def __init__(self):
                self.calls = []
            def require_root(self):
                pass
            def run(self, argv, **kwargs):
                self.calls.append(argv)
                if argv[0].endswith('dpkg-query'):
                    return ''.join(row['name'] + '\t' + row['version'] + '\t' + row['architecture'] + '\tinstall ok installed\n' for row in manifest['components'])
                return ''
        runner = FakeRunner()
        adapter = payload.PreparedPayload(bundle, manifest_sha256=manifest_sha, runner=runner,
            finalizer=lambda *_: {}, target_guard=lambda *_: True,mount_base=self.root/'operation-logs')
        self.assertTrue(adapter.verify_payload(plan)['verified'])
        target = self.root / 'empty-fake-target'
        target.mkdir()
        with self.assertRaisesRegex(payload.PayloadError, 'finalizer_incomplete'):
            adapter.install_payload(target, plan)
        self.assertTrue(any('--unpack' in argv for argv in runner.calls))
        self.assertTrue(all('--root=' + str(target) in argv or argv[0].endswith('dpkg-query') for argv in runner.calls))
        self.assertEqual(list(target.iterdir()), [])  # fake runner wrote nothing
        for argv in runner.calls:
            if argv[0].endswith('/dpkg'):
                log=Path(next(arg.removeprefix('--log=') for arg in argv if arg.startswith('--log=')))
                self.assertTrue(log.is_relative_to(self.root/'operation-logs'))
                self.assertFalse(log.is_relative_to(target))
                self.assertEqual(log.parent.stat().st_mode&0o777,0o700)
        adapter.finalizer = lambda *_: {'checks': {check: {'passed': True, 'report_sha256': 'a' * 64}
            for check in payload.CHECKS}, 'generated_entries': {}, 'image_manifest_sha256': 'b' * 64}
        with self.assertRaisesRegex(payload.PayloadError, 'finalizer_failed'):
            adapter.install_payload(target, plan)  # bare success markers are insufficient
        archive = bundle / 'archives/fixture-base_1.0_all.deb'
        archive.chmod(0o600)
        archive.write_bytes(b'tampered copied bundle')
        with self.assertRaisesRegex(payload.PayloadError, 'custody_changed'):
            adapter.verify_payload(plan)


if __name__ == '__main__':
    unittest.main()
