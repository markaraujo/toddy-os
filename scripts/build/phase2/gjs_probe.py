"""Real CLI ES module, GLib event delivery, Gio refusal and invalid JS checks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def run(binary, directory, env):
    directory.mkdir()
    missing = directory / 'must-remain-absent'
    assert not missing.exists()
    module = directory / 'consumer.mjs'
    module.write_text("""import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
const file = Gio.File.new_for_path(%s);
let refused = false;
try { file.load_contents(null); }
catch (error) { refused = error.matches(Gio.io_error_quark(), Gio.IOErrorEnum.NOT_FOUND); }
if (!refused) throw Error('Missing-file refusal was not typed');
const loop = GLib.MainLoop.new(null, false);
let observed = 0;
GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
  observed = 6 * 7;
  loop.quit();
  return GLib.SOURCE_REMOVE;
});
loop.run();
if (observed !== 42) throw Error('Native GLib callback missing');
print('native ES module/GI/GLib event/Gio refusal=42');
""" % json.dumps(str(missing)))
    records = []
    for name, args in [('version', [binary, '--version']), ('module', [binary, '-m', str(module)]),
                       ('invalid', [binary, '-c', 'function {'])]:
        with (directory / (name + '.stdout')).open('xb') as stdout, (directory / (name + '.stderr')).open('xb') as stderr:
            result = subprocess.run(args, env=env, stdout=stdout, stderr=stderr, timeout=30)
        records.append({'name': name, 'exit': result.returncode,
                        'stdout_sha256': hashlib.sha256((directory / (name + '.stdout')).read_bytes()).hexdigest(),
                        'stderr_sha256': hashlib.sha256((directory / (name + '.stderr')).read_bytes()).hexdigest()})
    assert records[0]['exit'] == records[1]['exit'] == 0
    assert '1.88.1' in (directory / 'version.stdout').read_text()
    assert 'native ES module/GI/GLib event/Gio refusal=42' in (directory / 'module.stdout').read_text()
    assert records[2]['exit'] != 0 and 'SyntaxError' in (directory / 'invalid.stderr').read_text()
    assert not missing.exists()
    return {'scope': 'Real GJS CLI ES module/native GLib event/typed Gio refusal and syntax refusal; no GTK/session acceptance',
            'records': records, 'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest()}


if __name__ == '__main__':
    assert os.getuid() == 101
    result = run('/stage/usr/bin/gjs', Path('/build/cli-probe-1'),
                 {**os.environ, 'LD_LIBRARY_PATH': '/stage/usr/lib',
                  'GI_TYPELIB_PATH': '/stage/usr/lib/gjs/girepository-1.0'})
    Path('/build/cli-probe-results.json').write_text(json.dumps(result, indent=2) + '\n')
