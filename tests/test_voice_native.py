"""Host source/fixture checks only; never compile/install or infer audio here."""
import hashlib,importlib.util,json,os,stat,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import voice_native as v
import voice_consumer as c

class NativeSourceTests(unittest.TestCase):
    def test_frozen_three_source_rows_and_immutable_model_revision(self):
        lock=json.loads((ROOT/'runtime/voice/native-inputs.lock.json').read_text())
        inputs={x['filename']:x for x in lock['artifacts']}
        rows=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
        for package,(ident,version,recipe,binary) in v.COMPONENTS.items():
            row=next(x for x in rows if x['name']==package)
            self.assertEqual(row['sha256'],inputs[row['filename']]['sha256'])
            self.assertEqual(row['url'],inputs[row['filename']]['url'])
            if package=='toddy-voice-model-base':
                self.assertEqual(row['version'],'5359861c739e955e79d9a303bcbc70fb988958b1')
                self.assertEqual(row['size'],147951465)
                self.assertNotIn('base-model',json.dumps(json.loads((ROOT/'config/phase2/desktop-runtime-roots.json').read_text())))
    def test_generation_rejects_traversal_and_unregistered_component(self):
        for component,generation in [('whisper-cpp','../escape'),('anything','1'),('whisper-cpp',''),('whisper-cpp','a'*33)]:
            with self.assertRaisesRegex(ValueError,'generation'):v.paths(component,generation)
    def test_transcript_metric_uses_actual_words_bilingual_accents_and_empty_refusal(self):
        self.assertEqual(c.word_error('Onde fica o banheiro?','Onde fica o banheiro.'),0)
        self.assertEqual(c.word_error('Olá português','Ola portugues'),0)
        self.assertEqual(c.word_error('the quick brown fox','the slow fox'),.5)
        with self.assertRaisesRegex(ValueError,'empty'):c.word_error('reference','')
    def test_root_catalog_requires_actual_native_process_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);prefix=base/'receipt'
            with patch.object(v,'prepared',return_value=(base,base,prefix,{})):
                with self.assertRaises(FileNotFoundError):v.catalog('whisper-cpp','1')
            self.assertFalse((base/'catalog.json').exists())
    def test_package_record_detects_bytes_owner_mode_and_symlink_tampering(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t);p=target/'payload';p.write_bytes(b'expected');info=p.stat()
            record={'installed':True,'payload':{'/payload':{'mode':info.st_mode,'sha256':hashlib.sha256(b'expected').hexdigest()}}}
            # This host test need not be root. Only fixture uid fields are patched;
            # production validator always requires UID/GID0.
            real=Path.lstat
            def fixture_lstat(path):
                row=real(path)
                if path==p:return os.stat_result((row.st_mode,row.st_ino,row.st_dev,row.st_nlink,0,0,row.st_size,row.st_atime,row.st_mtime,row.st_ctime))
                return row
            with patch.object(Path,'lstat',fixture_lstat):
                v.verify_package_record(record,target)
                p.write_bytes(b'altered')
                with self.assertRaisesRegex(ValueError,'hash'):v.verify_package_record(record,target)
                p.write_bytes(b'expected');p.chmod(0o600)
                with self.assertRaisesRegex(ValueError,'ownership'):v.verify_package_record(record,target)
    def test_elf_search_path_and_wrong_architecture_fail_before_dependency_execution(self):
        headers=['Machine: AArch64\nType: EXEC','Machine: Advanced Micro Devices X86-64\nType: DYN']
        with patch.object(v.subprocess,'check_output',return_value=headers[0]):
            with self.assertRaisesRegex(ValueError,'architecture'):v.elf_dependencies(Path('/fixture'))
        with patch.object(v.subprocess,'check_output',side_effect=[headers[1],'(RUNPATH) [/build/compile]']):
            with self.assertRaisesRegex(ValueError,'search_path'):v.elf_dependencies(Path('/fixture'))
    def test_espeak_install_rpath_is_disabled_without_weakening_native_elf_guard(self):
        recipe=(ROOT/'scripts/build/phase2/voice-espeak-build.sh').read_text()
        self.assertIn('-DCMAKE_SKIP_INSTALL_RPATH=ON',recipe)
        self.assertIn('-DCMAKE_INSTALL_PREFIX=/usr',recipe)
        for path in ('/usr/lib','/build/compile'):
            with self.subTest(path=path),patch.object(v.subprocess,'check_output',side_effect=['Machine: Advanced Micro Devices X86-64\nType: DYN','(RUNPATH) ['+path+']']):
                with self.assertRaisesRegex(ValueError,'embedded_search_path'):v.elf_dependencies(Path('/source-fixture'))

    def test_job_existing_marker_prevents_uncertain_replay(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);prefix=base/'receipt';(base/'receipt.prepared.json').write_text('{}');(base/'receipt.build.json').write_text('{"state":"running-no-replay"}')
            with patch.object(v,'prepared',return_value=(base,base,prefix,{})),patch.object(v.subprocess,'run') as run:
                with self.assertRaises(FileExistsError):v.isolated_job('whisper-cpp','1','build')
                run.assert_not_called()
    def test_root_artifact_refuses_symlinks_and_group_write(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'artifact';path.write_text('fixture');link=path.with_name('link');link.symlink_to(path)
            with self.assertRaisesRegex(ValueError,'root_owned'):v.regular(link)
            path.chmod(0o666)
            with self.assertRaisesRegex(ValueError,'root_owned'):v.regular(path)
    def test_model_prepare_reuses_exact_inputs_and_refuses_existing_generation(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t);cache=target/'sources';cache.mkdir();logs=target/'logs';logs.mkdir()
            rows=[]
            for ident,name,data in [('whisper-base-model','ggml-base.bin',b'fixture model bytes'),('whisper-original-license','original.txt',b'fixture original license'),('whisper-model-card','card.txt',b'fixture model card')]:
                (cache/name).write_bytes(data);(cache/name).chmod(0o644)
                rows.append({'id':ident,'filename':name,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'url':'https://fixture.invalid/'+name})
            lock={'artifacts':rows,'model_terms':{'license':'MIT','scope':'Tiny source test fixture; no native acceptance'}}
            with patch.object(v,'T',target),patch.object(v,'L',logs),patch.object(v,'R',ROOT),patch.object(v,'load_lock',return_value=lock),patch.object(v,'reserve'),patch.object(v.os,'chown'):
                proof=v.prepare('toddy-voice-model-base','fixture',cache)
                self.assertEqual(proof['input']['sha256'],rows[0]['sha256'])
                source,work,prefix=v.paths('toddy-voice-model-base','fixture')
                self.assertEqual((work/'stage/usr/share/toddy/voice/models/ggml-base.bin').read_bytes(),b'fixture model bytes')
                with self.assertRaisesRegex(ValueError,'generation_exists'):v.prepare('toddy-voice-model-base','fixture',cache)
                v.verify_file(work/'stage/usr/share/toddy/voice/models/ggml-base.bin',rows[0])
                # Even valid model bytes cannot qualify with changed original terms.
                legal=work/'stage/usr/share/doc/toddy-voice-model-base/original.txt';legal.write_bytes(b'altered')
                with patch.object(v,'prepared',return_value=(source,work,prefix,proof)):
                    with self.assertRaisesRegex(ValueError,'integrity'):v.qualify('toddy-voice-model-base','fixture')
                self.assertFalse(Path(str(prefix)+'.qualified.json').exists())
    def test_record_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'record_path'):
                v.verify_package_record({'installed':True,'payload':{'/../escape':{}}},Path(t))
    def test_entrypoints_never_download_or_open_audio(self):
        for phase in ('prepare','qualify','install','check'):
            text=(ROOT/f'scripts/build/phase2/voice-{phase}.sh').read_text()
            self.assertIn(f'voice_native.py {phase}',text)
            self.assertNotIn('curl',text);self.assertNotIn('pw-record',text)
        script=(ROOT/'scripts/build/phase2/voice_native.py').read_text()
        self.assertIn('guard_target',script)
        self.assertIn('fcntl.LOCK_EX|fcntl.LOCK_NB',script)
        self.assertNotIn('urllib',script)

if __name__=='__main__':unittest.main()
