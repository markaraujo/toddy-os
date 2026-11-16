"""Exact B01 stage reuse fixtures; no native Calamares/install execution."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import tarfile
import io
import unittest
from unittest.mock import Mock,patch

BUILD=Path(__file__).resolve().parents[1]/'scripts/build'
import sys
sys.path[:0]=[str(BUILD),str(BUILD/'phase2')]
import calamares_native as c


class CalamaresPackageTests(unittest.TestCase):
    def test_exact_frozen_runtime_providers_and_version(self):
        self.assertEqual(c.VERSION,'3.4.3-1+toddy1')
        self.assertEqual(len(c.PROVIDERS),7)
        self.assertIn('gcc-runtime (= 16.2.0-1+toddy1)',c.DEPENDS)
        self.assertIn('qtbase (= 6.11.2-1+toddy2)',c.DEPENDS)
        self.assertEqual(c.ACCEPTED.name,'stage')
        self.assertIn('calamares-probe-1',str(c.ACCEPTED))
        self.assertEqual(c.STAGE_SHA,'439015aa8fd7c97674e0577862bfd8f21999a1fcb09a67976e848347334b2c03')

    def test_native_absence_must_be_established_before_first_install(self):
        with patch.object(c,'accepted_stage',return_value={}),patch.object(c,'source_configuration',return_value={}),patch.object(c,'dependency_state',return_value={}),patch.object(c,'elf_dependencies',return_value={}),patch.object(c.subprocess,'run',return_value=Mock(returncode=1)):
            c.qualify()
            with patch.object(c.subprocess,'run',return_value=Mock(returncode=0)):
                with self.assertRaisesRegex(ValueError,'absence not established'):c.qualify()
            with patch.object(c.subprocess,'run',return_value=Mock(returncode=2)):
                with self.assertRaisesRegex(ValueError,'absence not established'):c.qualify()

    def test_accepted_stage_mismatch_fails_before_promotion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);evidence=root/'docs/evidence';evidence.mkdir(parents=True)
            (evidence/'B01-calamares-native-probe.json').write_text(json.dumps({'command_exit':0,'consumer_job':'calamares-probe-4','stage_manifest_sha256':c.STAGE_SHA}))
            (root/'calamares-probe-4.exit').write_text('0\n')
            with patch.object(c,'ROOT',root),patch.object(c,'LOG',root),patch.object(c,'digest',return_value=c.SOURCE_SHA),patch('verify_stage.inspect_stage',return_value={'manifest_sha256':'a'*64,'entries':{}}):
                with self.assertRaisesRegex(ValueError,'stage changed'):c.accepted_stage()

    def test_elf_owner_is_declared_unambiguous_and_current_bytes_match_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/'target';stage=root/'stage';records=root/'records'
            records.mkdir();info=target/'var/lib/dpkg/info';info.mkdir(parents=True)
            library=target/'usr/lib/libc.so.6';library.parent.mkdir(parents=True);library.write_bytes(b'provider fixture')
            (info/'glibc.list').write_text('/usr/lib/libc.so.6\n')
            (records/'glibc_1_amd64.json').write_text(json.dumps({'payload':{'/usr/lib/libc.so.6':{'sha256':c.digest(library)}}}))
            (stage/'usr/lib').mkdir(parents=True)
            for name in ('one','two','three'):(stage/'usr/lib'/name).write_bytes(b'\x7fELF fixture')
            with patch.object(c,'TARGET',target),patch.object(c,'RECORDS',records),patch.object(c,'PROVIDERS',{'glibc':'1'}),patch.object(c.subprocess,'check_output',return_value='0 (NEEDED) Shared library: [libc.so.6]\n'):
                self.assertEqual(c.elf_dependencies(stage)['providers'],['glibc'])
                library.write_bytes(b'changed provider')
                with self.assertRaisesRegex(ValueError,'provider bytes'):c.elf_dependencies(stage)
                (info/'foreign.list').write_text('/usr/lib/libc.so.6\n')
                with self.assertRaisesRegex(ValueError,'ambiguous'):c.elf_dependencies(stage)

    def test_source_archive_and_all_skipped_module_configuration_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary);source=target/'source';(source/'src/modules/dummy').mkdir(parents=True)
            (source/'src/base.cpp').write_bytes(b'frozen source')
            (target/'sources').mkdir();work=target/'work';(work/'compile').mkdir(parents=True)
            values={'INSTALL_CONFIG':'OFF','INSTALL_POLKIT':'OFF','WITH_PYBIND11':'ON','WITH_PYTHON':'ON',
                'WITH_QML':'OFF','CMAKE_HOME_DIRECTORY':'/src','SKIP_MODULES':'dummy'}
            cache=work/'compile/CMakeCache.txt'
            def write_cache():cache.write_text(''.join(k+':BOOL='+v+'\n' for k,v in values.items()))
            write_cache()
            with tarfile.open(target/'sources'/c.ARCHIVE,'w:gz') as archive:
                info=tarfile.TarInfo('calamares-3.4.3/src/base.cpp');info.size=len(b'frozen source');archive.addfile(info,io.BytesIO(b'frozen source'))
            with patch.object(c,'TARGET',target),patch.object(c,'SOURCE',source),patch.object(c,'ACCEPTED',work/'stage'):
                self.assertEqual(c.source_configuration()['frozen_source_files'],1)
                values['INSTALL_POLKIT']='ON';write_cache()
                with self.assertRaisesRegex(ValueError,'configuration differs'):c.source_configuration()
                values['INSTALL_POLKIT']='OFF';write_cache();(source/'src/base.cpp').write_bytes(b'unknown patch')
                with self.assertRaisesRegex(ValueError,'undeclared source patch'):c.source_configuration()

    def test_transaction_requires_actual_persisted_recipe_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            marker=root/'b12-calamares-native-1.running.json'
            record={'step':c.STEP,'user':'root','recipe_pid':os.getppid(),'recipe_sha256':'a'*64,'postcheck_sha256':'a'*64}
            marker.write_text(json.dumps(record))
            original=Path.read_bytes
            def read(path):return marker.read_text().encode() if str(path)=='/var/log/toddy/build/'+marker.name else original(path)
            with patch.object(c,'digest',return_value='a'*64),patch.object(Path,'read_bytes',read):
                c.transaction('install')
                with self.assertRaisesRegex(ValueError,'completion'):c.transaction('postcheck')
                record['recipe_exit']=0;marker.write_text(json.dumps(record));c.transaction('postcheck')

    def test_failed_preflight_never_promotes_or_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage=Path(temporary)/'new';receipt=Path(temporary)/'receipt.json'
            with patch.object(c,'STAGE',stage),patch.object(c,'RECEIPT',receipt),patch.object(c,'transaction'),patch.object(c,'qualify',side_effect=ValueError('fixture missing native provider')),patch.object(c.shutil,'copytree') as copy,patch.object(c.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'missing native provider'):c.install()
                copy.assert_not_called();run.assert_not_called();self.assertFalse(stage.exists());self.assertFalse(receipt.exists())


if __name__=='__main__':unittest.main()
