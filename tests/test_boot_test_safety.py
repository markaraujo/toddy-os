import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HOST = Path(__file__).resolve().parents[1] / 'scripts/host'
sys.path.insert(0, str(HOST))
spec = importlib.util.spec_from_file_location('toddy_boot_test', HOST / 'boot_test.py')
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)
sys.path.pop(0)


class BootTestSafety(unittest.TestCase):
    def fixture(self, folder):
        name = 'h09-ready'
        data = {'name': name, 'disks': {}}
        for role in ('builder', 'target'):
            filename = f'{name}-{role}.qcow2'
            (folder / filename).write_bytes(b'guard fixture only')
            data['disks'][role] = {'file': filename, 'sha256': 'a' * 64}
        (folder / (name + '.json')).write_text(json.dumps(data))
        return name, data

    def test_checkpoint_rejects_external_disk_and_mismatched_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            name, data = self.fixture(folder)
            self.assertEqual(boot.read_checkpoint(folder, name)[1].parent, folder)
            for filename in ('/dev/sda', '../lfs-target.qcow2', 'lfs-target.qcow2'):
                data['disks']['target']['file'] = filename
                (folder / (name + '.json')).write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    boot.read_checkpoint(folder, name)
            with self.assertRaises(ValueError):
                boot.read_checkpoint(folder, '../h09-ready')

    def test_checkpoint_rejects_redirected_disk_and_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory).resolve()
            name, data = self.fixture(folder)
            target = folder / data['disks']['target']['file']
            target.unlink()
            target.symlink_to(folder / data['disks']['builder']['file'])
            with self.assertRaises(ValueError):
                boot.read_checkpoint(folder, name)
            redirected = folder / 'redirected'
            redirected.symlink_to(folder, target_is_directory=True)
            with self.assertRaises(ValueError):
                boot.read_checkpoint(redirected, name)

    def test_no_boot_success_from_partial_or_wrong_environment_reports(self):
        report = {'firmware': 'bios', 'kernel': '7.1.8-toddy', 'pid1': 'systemd',
                  'virtualization': 'kvm', 'native_c_execution': True,
                  'dummy_load_unload': True, 'root_source': '/dev/vda4',
                  'native_linkage': '/lib64/ld-linux-x86-64.so.2'}
        valid = 'TODDY_NATIVE_BOOT_OK ' + json.dumps(report)
        self.assertEqual(boot.parse_report(valid, 'bios'), report)
        for serial, firmware in [('', 'bios'), (valid, 'uefi'),
                                 (valid + '\nTODDY_NATIVE_BOOT_FAIL error', 'bios')]:
            with self.assertRaises(ValueError):
                boot.parse_report(serial, firmware)
        report['dummy_load_unload'] = False
        with self.assertRaises(ValueError):
            boot.parse_report('TODDY_NATIVE_BOOT_OK ' + json.dumps(report), 'bios')
        report['dummy_load_unload'] = True
        report['native_linkage'] += ' libc.so.6 => /tools/lib/libc.so.6'
        with self.assertRaises(ValueError):
            boot.parse_report('TODDY_NATIVE_BOOT_OK ' + json.dumps(report), 'bios')

    def test_qemu_rejects_unreviewed_payload_set_and_firmware(self):
        payloads = {key: b'public fixture' for key in boot.PAYLOADS}
        for firmware in ('bios', 'uefi'):
            args = boot.qemu_arguments(firmware, payloads)
            self.assertIn('file=/work/target.qcow2,if=none,id=root,format=qcow2', args)
            self.assertIn('virtio-blk-pci,drive=root,serial=TODDY-BOOT-TEST', args)
        with self.assertRaises(ValueError):
            boot.qemu_arguments('uefi', {**payloads, 'unreviewed': b'no'})
        with self.assertRaises(ValueError):
            boot.qemu_arguments('unknown', payloads)


if __name__ == '__main__':
    unittest.main()


class NativeEvidenceStream(unittest.TestCase):
    def stream(self):
        import base64, hashlib, json, zlib
        raw=json.dumps({'complete': False, 'results': [{'test':'native-case','exit':1}]}).encode()
        data=base64.b64encode(zlib.compress(raw)).decode()
        summary={'chunks':1,'report_sha256':hashlib.sha256(raw).hexdigest()}
        return 'TODDY_NATIVE_REGRESSIONS_DATA 0 '+data+'\nTODDY_NATIVE_REGRESSIONS_RESULT '+json.dumps(summary)+'\n'

    def test_raw_failure_evidence_is_decoded_without_becoming_acceptance(self):
        report, summary=boot.decode_regressions(self.stream())
        self.assertIs(report['complete'],False)
        self.assertEqual(report['results'][0]['exit'],1)

    def test_missing_conflicting_and_corrupted_chunks_are_rejected(self):
        stream=self.stream()
        missing=stream.split('\n',1)[1]
        conflicting=stream+'TODDY_NATIVE_REGRESSIONS_DATA 0 ZmFrZQ==\n'
        import json
        line=stream.splitlines()[-1]
        summary=json.loads(line.split('TODDY_NATIVE_REGRESSIONS_RESULT ',1)[1])
        summary['report_sha256']='0'*64
        corrupted=stream.splitlines()[0]+'\nTODDY_NATIVE_REGRESSIONS_RESULT '+json.dumps(summary)+'\n'
        for case in (missing,conflicting,corrupted):
            with self.subTest(case=case),self.assertRaises(ValueError):
                boot.decode_regressions(case)
