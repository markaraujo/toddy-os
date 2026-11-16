"""Owned sealed FD and actual child framing/Stop; no model/provider qualification."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from engine import EngineAdapter, EngineError


@unittest.skipIf(os.geteuid() == 0, 'engine deliberately runs without root')
class EngineAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.bootstrap = {'version': 1, 'profile_revision': 'a' * 64,
            'profile': {'schema_version': 1, 'budgets': {'task_deadline_seconds': 3, 'max_tool_calls': 1}},
            'connection': {'credential': 'dummy-secret-private-only'}, 'catalog': {},
            'system_prompt': 'Synthetic process only.', 'remote_consent': False,
            'tools': [{'name': 'read-file'}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_actual_private_bootstrap_memfd_owned_bounded_and_sealed(self):
        descriptor = EngineAdapter._bootstrap_fd(self.bootstrap)
        try:
            info = os.fstat(descriptor)
            self.assertEqual(info.st_uid, os.getuid()); self.assertEqual(info.st_mode & 0o777, 0o600)
            required = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
            self.assertEqual(fcntl.fcntl(descriptor, fcntl.F_GET_SEALS) & required, required)
            self.assertEqual(json.loads(os.read(descriptor, 65536))['connection'], self.bootstrap['connection'])
            with self.assertRaises(OSError):
                os.write(descriptor, b'cannot change prepared bytes')
        finally:
            os.close(descriptor)
        with self.assertRaisesRegex(EngineError, 'engine_bootstrap_limit'):
            EngineAdapter._bootstrap_fd({'payload': 'x' * 65536})

    def worker(self, behavior):
        if not shutil.which('node'):
            self.skipTest('optional Node process fixture unavailable')
        script = self.directory / 'synthetic.mjs'
        framing = (ROOT / 'runtime/engine/framing.mjs').as_uri()
        script.write_text('''import {readFileSync,closeSync} from 'node:fs';
import {readFrames,writeFrame} from ''' + json.dumps(framing) + ''';
const fd=Number(process.env.TODDY_BOOTSTRAP_FD); const b=JSON.parse(readFileSync(fd)); closeSync(fd);
if(process.argv.some(a=>a.includes(b.connection.credential)) ||
   Object.values(process.env).some(a=>a.includes(b.connection.credential))) throw Error('bad private fixture');
const hello={version:1,kind:'hello',worker_id:'worker-runtime',
 capabilities:['agent-runtime-v1','runtime-tool-result-v1','single-run','cancel'],max_frame:1048576};
await writeFrame(process.stdout,hello);
for await(const run of readFrames(process.stdin)) {
 const base={version:1,worker_id:'worker-runtime',run_id:run.run_id,request_id:run.request_id};
''' + behavior + '\n}\n')
        return EngineAdapter(shutil.which('node'), script)

    def test_actual_process_text_has_no_credential_and_clean_finish(self):
        adapter = self.worker("""if(run.kind==='run') {
 await writeFrame(process.stdout,{...base,kind:'text',seq:1,text:'Actual child event.'});
 await writeFrame(process.stdout,{...base,kind:'done',seq:2,state:'completed',code:'completed'});
}""")
        text = []
        result = adapter.run(self.bootstrap, 'run-one', 'request-one', 'Synthetic request',
                             on_tool=lambda *_: self.fail(), on_text=text.append)
        self.assertEqual(result['state'], 'completed'); self.assertEqual(text, ['Actual child event.'])
        self.assertNotIn('dummy-secret', json.dumps(result) + ''.join(text))

    def test_actual_process_cancel_while_silent_has_bounded_cleanup(self):
        adapter = self.worker("""if(run.kind==='cancel') {
 await writeFrame(process.stdout,{...base,kind:'done',seq:1,state:'canceled',code:'canceled'});
}""")
        canceled = threading.Event()
        timer = threading.Timer(.1, canceled.set); timer.start()
        start = time.monotonic()
        try:
            result = adapter.run(self.bootstrap, 'run-one', 'request-one', 'Synthetic request',
                                 on_tool=lambda *_: self.fail(), canceled=canceled.is_set)
        finally:
            timer.cancel()
        self.assertEqual(result['state'], 'canceled')
        self.assertLess(time.monotonic() - start, 2)

    def test_wrong_sequence_and_tool_rejected_without_dispatch_or_raw_stderr(self):
        for behavior, code in [
            ("if(run.kind==='run') await writeFrame(process.stdout,{...base,kind:'done',seq:2,state:'completed',code:'completed'});", 'engine_event_identity'),
            ("if(run.kind==='run') {process.stderr.write(b.connection.credential); await writeFrame(process.stdout,{...base,kind:'tool_request',seq:1,tool_call_id:'tool-1',tool:'undeclared',arguments:{}});}", 'engine_tool_limit'),
        ]:
            with self.subTest(code=code):
                adapter = self.worker(behavior)
                with self.assertRaisesRegex(EngineError, code) as raised:
                    adapter.run(self.bootstrap, 'run-one', 'request-one', 'Synthetic request', on_tool=lambda *_: self.fail())
                self.assertNotIn('dummy-secret', str(raised.exception))

    def test_unavailable_engine_does_not_call_tool(self):
        adapter = EngineAdapter('/definitely-unavailable-node', self.directory / 'missing.mjs')
        with self.assertRaisesRegex(EngineError, 'engine_disconnected'):
            adapter.run(self.bootstrap, 'run-one', 'request-one', 'Synthetic request', on_tool=lambda *_: self.fail())


if __name__ == '__main__':
    unittest.main(verbosity=2)
