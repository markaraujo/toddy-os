"""Pure geometry/CRC/guard fixtures. No QMP, VM, device write or resize execution."""
import binascii
import copy
import importlib.util
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/host'))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
geo=module('growth_geometry_fixture','scripts/build/phase2/candidate_target_geometry.py')
guest=module('growth_guest_fixture','scripts/build/phase2/grow_candidate_target.py')
host=module('growth_host_fixture','scripts/host/phase2_candidate_target_grow.py')


class GrowthTests(unittest.TestCase):
    def test_only_exact_ubuntu_syslog_parent_is_allowed(self):
        mode=stat.S_IFDIR|0o775
        group=guest.grp.getgrnam('syslog').gr_gid
        valid=SimpleNamespace(st_uid=0,st_gid=group,st_mode=mode)
        self.assertTrue(guest.trusted_log_parent(Path('/var/log'),valid))
        for path,info in ((Path('/var'),valid),
                          (Path('/var/log'),SimpleNamespace(st_uid=1000,st_gid=group,st_mode=mode)),
                          (Path('/var/log'),SimpleNamespace(st_uid=0,st_gid=group,st_mode=stat.S_IFDIR|0o777)),
                          (Path('/var/log'),SimpleNamespace(st_uid=0,st_gid=0,st_mode=mode))):
            self.assertFalse(guest.trusted_log_parent(path,info))
    def test_exact_growth_preserves_first_three_partitions_and_root_start_uuid(self):
        old=geo.table(geo.OLD);new=geo.table(geo.NEW)
        self.assertEqual(geo.NEW,219043332096);self.assertEqual(geo.NEW-geo.OLD,24*1024**3)
        self.assertEqual(old['partitions'][:3],new['partitions'][:3])
        for key in ('node','start','type','uuid','name'):self.assertEqual(old['partitions'][3][key],new['partitions'][3][key])
        self.assertEqual(geo.partition_bytes(geo.NEW)-geo.partition_bytes(geo.OLD),24*1024**3)
        self.assertEqual((geo.NEW//512)-(new['partitions'][3]['start']+new['partitions'][3]['size']),2048)
        changed=copy.deepcopy(new);changed['partitions'][3]['start']+=1
        with self.assertRaisesRegex(ValueError,'Exact target GPT'):geo.verify_table(changed,geo.NEW)
        with self.assertRaises(ValueError):geo.table(224*1024**3)

    def test_both_gpt_crcs_and_entry_replicas_are_verified(self):
        size=geo.NEW;sectors=size//512;entries=b'\0'*(128*128);blocks={2*512:entries,(sectors-33)*512:entries}
        for lba,alternate,entries_lba in ((1,sectors-1,2),(sectors-1,1,sectors-33)):
            header=bytearray(512);header[:8]=b'EFI PART';struct.pack_into('<II',header,8,0x10000,92)
            struct.pack_into('<QQQQ',header,24,lba,alternate,34,sectors-34)
            struct.pack_into('<QIII',header,72,entries_lba,128,128,binascii.crc32(entries)&0xffffffff)
            struct.pack_into('<I',header,16,binascii.crc32(header[:92])&0xffffffff);blocks[lba*512]=bytes(header)
        read=lambda count,offset:blocks[offset][:count]
        self.assertEqual(set(geo.gpt(read,size)),{'primary_sha256','backup_sha256','entries_sha256'})
        blocks[2*512]=b'x'+entries[1:]
        with self.assertRaisesRegex(ValueError,'array CRC'):geo.gpt(read,size)

    def test_full24gib_host_allowance_is_additional_to_absolute_cold_floor(self):
        required=host.COLD+geo.NEW-geo.OLD
        host.capacity(required)
        with self.assertRaisesRegex(ValueError,'all24GiB'):host.capacity(required-1)

    def test_qmp_accepts_only_exact_candidate_lfs_top_overlay(self):
        client=host.QMP.__new__(host.QMP)
        row={'device':'lfs','inserted':{'image':{'filename':'/vm/phase2-candidate/lfs-target.qcow2','format':'qcow2','virtual-size':geo.OLD,'backing-filename':'/vm/phase2/lfs-target.qcow2'}}}
        client.call=lambda *_:[row];self.assertEqual(client.block(geo.OLD),row)
        row['inserted']['image']['filename']='/vm/phase2/lfs-target.qcow2'
        with self.assertRaisesRegex(ValueError,'top-overlay'):client.block(geo.OLD)

    def test_guest_wrong_uid_and_unprivileged_receipt_fail_before_device_commands(self):
        with patch.object(guest.os,'getuid',return_value=1000),patch.object(guest,'command') as command:
            with self.assertRaisesRegex(ValueError,'virtual builder root'):guest.identity()
            command.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'qualified.json';path.write_text('{}')
            with patch.object(guest,'QUALIFIED',path),patch.object(guest,'identity') as identity:
                with self.assertRaises(ValueError):guest.checked_completed()
                identity.assert_not_called()

    def test_actual_shell_guard_keeps180_and_requires_completed204_validator(self):
        script=ROOT/'scripts/build/target.sh'
        for size,expected,called in ((geo.OLD,0,False),(geo.NEW,1,True),(224*1024**3,1,False)):
            source='''hostname(){ echo toddy-builder; }
systemd-detect-virt(){ echo kvm; }
lsblk(){ case "${@: -1}" in /dev/vdb) echo TODDY-LFS-TARGET;; /dev/vda) echo TODDY-BUILDER;; esac; }
findmnt(){ echo /dev/vda1; }
blockdev(){ echo SIZE; }
python3(){ echo COMPLETED_VALIDATOR_REQUIRED; return 1; }
source "$1"
if guard_guest; then exit 0; else exit 1; fi
'''.replace('SIZE',str(size))
            result=subprocess.run(['bash','-c',source,'source-guard-fixture',str(script)],capture_output=True,text=True)
            self.assertEqual(result.returncode,expected,result.stderr);self.assertEqual('COMPLETED_VALIDATOR_REQUIRED' in result.stdout,called)

    def test_direct_isolated_script_imports_and_exact_non_destructive_commands(self):
        for path in ('scripts/build/phase2/grow_candidate_target.py','scripts/host/phase2_candidate_target_grow.py'):
            result=subprocess.run(['python3','-I',str(ROOT/path),'--help'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        source=(ROOT/'scripts/build/phase2/grow_candidate_target.py').read_text()
        self.assertIn("['partx','--update','--nr','4','/dev/vdb']",source)
        self.assertIn('--wipe=never',source);self.assertIn('run_step.snapshot()',source)
        self.assertNotIn('mkfs',source);self.assertNotIn('sgdisk',source)


if __name__=='__main__':unittest.main()
