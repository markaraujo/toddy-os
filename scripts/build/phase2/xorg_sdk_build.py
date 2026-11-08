"""Build pinned headless Xorg validation dependencies in independent stages."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def entries(root):
    rows = {}
    for path in sorted(root.rglob('*')):
        key = str(path.relative_to(root))
        if path.is_symlink():
            rows[key] = {'symlink': os.readlink(path)}
        elif path.is_file():
            rows[key] = {'sha256': digest(path), 'size': path.stat().st_size}
    return rows


def main():
    assert os.getuid() == 101
    root = Path('/build/xorg-sdk')
    assert not root.exists() and not list(Path('/stage').iterdir()), 'No replay'
    assert os.statvfs('/build').f_bavail * os.statvfs('/build').f_frsize >= 18 * 1024**3
    root.mkdir()
    for name in ['source', 'compile', 'logs', 'bootstrap']:
        (root/name).mkdir()
    prefix = str(root/'bootstrap/usr')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               PKG_CONFIG_PATH=prefix+'/lib/pkgconfig:'+prefix+'/share/pkgconfig',
               CPPFLAGS='-I'+prefix+'/include',
               LDFLAGS='-L'+prefix+'/lib -Wl,-rpath-link,'+prefix+'/lib',
               LD_LIBRARY_PATH=prefix+'/lib',
               PYTHONPATH=prefix+'/lib/python3.14/site-packages',
               ACLOCAL_PATH=prefix+'/share/aclocal', SOURCE_DATE_EPOCH='1780340400')
    config = json.loads(Path('/src/toddy-sdk.json').read_text())
    results = []
    for package in config['packages']:
        name = package['name']
        source = root/'source'/name
        shutil.copytree(Path('/src')/package['source_root'], source, symlinks=True)
        build = root/'compile'/name
        stage = Path('/stage')/name
        log = root/'logs'/(name+'.log')
        commands = []

        def run(command, cwd, extra=None):
            commands.append(command)
            with log.open('ab') as output:
                output.write((json.dumps(command)+'\n').encode()); output.flush()
                result = subprocess.run(command, cwd=cwd, env=dict(env, **(extra or {})),
                                        stdout=output, stderr=subprocess.STDOUT)
            receipt = root/'logs'/(name+'.command-'+str(len(commands))+'.exit')
            receipt.write_text(str(result.returncode)+'\n')
            assert result.returncode == 0, name+': '+str(command)+'; inspect '+str(log)

        if package['build_system'] == 'meson':
            run(['meson', 'setup', str(build), str(source), '--prefix=/usr', '--libdir=lib',
                 '--buildtype=release', '--wrap-mode=nofallback', *package['options']], root)
            run(['ninja', '-C', str(build), '-j4'], root)
            run(['meson', 'test', '-C', str(build), '--no-rebuild', '--print-errorlogs',
                 '--logbase', 'toddy-tests'], root)
            run(['ninja', '-C', str(build), 'install'], root, {'DESTDIR': str(stage)})
        else:
            build.mkdir()
            run([str(source/'configure'), '--prefix=/usr', '--libdir=/usr/lib',
                 '--disable-static', '--docdir=/usr/share/doc/'+name+'-'+package['version'],
                 *package['options']], build)
            run(['make', '-j4'], build)
            run(['make', '-j4', 'check'], build)
            run(['make', 'DESTDIR='+str(stage), 'install'], build)
        removed = []
        for path in stage.rglob('*.la'):
            removed.append(str(path.relative_to(stage))); path.unlink()
        # Only the private SDK uses relocated pkg-config data. The product stage
        # retains its frozen /usr prefix and cannot refer to temporary work paths.
        for path in stage.rglob('*.pc'):
            if path.is_file():
                body = path.read_text().replace(prefix, '/usr')
                assert '/build/' not in body and '/stage/' not in body
                path.write_text(body)
        payload = entries(stage)
        assert payload and all(p.startswith('usr/') for p in payload)
        elf_count = 0
        for path in stage.rglob('*'):
            if not path.is_file() or path.is_symlink():
                continue
            with path.open('rb') as stream:
                elf = stream.read(4) == b'\x7fELF'
            if elf:
                dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
                assert '(RPATH)' not in dynamic and '(RUNPATH)' not in dynamic, str(path)
                elf_count += 1
        for path in sorted(stage.rglob('*')):
            destination = root/'bootstrap'/path.relative_to(stage)
            if path.is_symlink():
                if destination.exists() or destination.is_symlink():
                    assert destination.is_symlink() and os.readlink(destination) == os.readlink(path)
                else:
                    destination.symlink_to(os.readlink(path))
            elif path.is_dir():
                destination.mkdir(exist_ok=True)
            else:
                data = path.read_bytes()
                if path.suffix == '.pc':
                    data = data.replace(b'/usr', prefix.encode())
                if destination.exists():
                    assert destination.read_bytes() == data, 'Conflicting private SDK ownership: '+str(path)
                else:
                    destination.write_bytes(data); shutil.copymode(path, destination)
        test_artifacts = []
        for path in sorted(build.rglob('*')):
            if path.is_file() and (path.suffix == '.trs' or path.name in
                                  ['test-suite.log', 'toddy-tests.json', 'testlog.json']):
                test_artifacts.append({'path': str(path), 'sha256': digest(path)})
        result = {'name': name, 'version': package['version'], 'source_sha256': package['source_sha256'],
                  'commands': commands, 'command_exits': [0]*len(commands), 'entries': payload,
                  'test_artifacts': test_artifacts, 'removed_libtool_archives': removed,
                  'elfs_without_runtime_build_paths': elf_count, 'log_sha256': digest(log)}
        if name == 'libxcb':
            text = (build/'config.log').read_text()
            assert 'check >=' in text
            result['optional_check_framework'] = 'Unavailable; Check-based unit tests not registered. make check exit alone is not unit acceptance.'
        results.append(result)
        (root/'results.partial.json').write_text(json.dumps(results, indent=2)+'\n')
        print(json.dumps({'package': name, 'build_check_stage_exit': 0, 'test_artifacts': len(test_artifacts)}), flush=True)
    env['PATH'] = prefix+'/bin:'+env['PATH']
    with (root/'probe.log').open('xb') as output:
        probe = subprocess.run(['python3', '/src/toddy-probe.py', prefix, '/build/xorg-sdk-consumer'],
                               env=env, stdout=output, stderr=subprocess.STDOUT)
    (root/'probe.exit').write_text(str(probe.returncode)+'\n')
    assert probe.returncode == 0, 'Headless native consumer failed'
    assert all(entries(Path('/stage')/r['name']) == r['entries'] for r in results)
    (root/'qualified.json').write_text(json.dumps({
        'scope': 'Headless staged Xorg SDK, not an X server/session/physical-input acceptance',
        'packages': results, 'config_sha256': digest(Path('/src/toddy-sdk.json')),
        'probe_exit': probe.returncode, 'probe_log_sha256': digest(root/'probe.log'),
        'consumer': json.loads(Path('/build/xorg-sdk-consumer/results.json').read_text())}, indent=2)+'\n')
    assert os.statvfs('/build').f_bavail * os.statvfs('/build').f_frsize >= 16 * 1024**3


if __name__ == '__main__':
    main()
