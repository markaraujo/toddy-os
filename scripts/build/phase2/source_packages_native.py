"""Fixed first native packaging of reviewed original-source payloads.

Run via run_step; archive/source/ownership checks are not UI acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/opt/toddy-build')
TARGET = Path('/mnt/lfs')
LOG = Path('/var/log/toddy/phase2')
VERSION = '0.2.0-1+toddy1'
PYTHON = 'python (>= 3.14.10-1+toddy2), python (<< 3.15), pygobject (= 3.56.3-1+toddy1)'
PACKAGES = {
    'branding': ('toddy-branding', ''),
    'assistant': ('toddy-assistant', PYTHON + ', gtk (= 4.22.4-1+toddy14), libadwaita (= 1.9.3-1+toddy1), libsecret (= 0.21.7-1+toddy1), polkit (= 127-1+toddy1), toddy-branding (= ' + VERSION + ')'),
    'agent': ('toddy-agent', PYTHON + ', sqlite (= 3.53.4-1+toddy1), nodejs (= 24.19.0-1+toddy1), toddy-assistant (= ' + VERSION + ')'),
    'voice': ('toddy-voice', PYTHON + ', toddy-assistant (= ' + VERSION + ')'),
    'integrations': ('toddy-integrations', PYTHON + ', bubblewrap (= 0.11.2-1+toddy1), at-spi2-core (= 2.60.6-1+toddy1), toddy-assistant (= ' + VERSION + ')'),
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def native(*args):
    return subprocess.check_output(['chroot', str(TARGET), *args], text=True).strip()


def paths(component):
    name, depends = PACKAGES[component]
    return name, depends, TARGET/'sources/stage'/('phase2-'+name+'-1'), LOG/(name+'-source-package-1.json')


def install(component):
    name, depends, stage, receipt = paths(component)
    assert not receipt.exists() and not stage.exists() and not stage.is_symlink()
    assert subprocess.run(['chroot', str(TARGET), 'dpkg-query', '-W', name], capture_output=True).returncode != 0
    from dependency_preflight import native as verify_dependencies
    if depends:
        verify_dependencies(depends)
    fs = os.statvfs(TARGET)
    assert fs.f_bavail*fs.f_frsize >= 16*1024**3 + 512*1024**2, 'Preserve target reserve before source payload staging'
    if component == 'branding':
        from branding_stage import stage_desktop
        manifest = stage_desktop(stage, ROOT)
    elif component == 'assistant':
        from assistant_package import stage as create
        manifest = create(ROOT, stage, version=VERSION)
    else:
        import optional_packages
        manifest = getattr(optional_packages, 'stage_'+component)(ROOT, stage, version=VERSION)
    # Existing packager rejects foreign-owned paths before native transaction.
    subprocess.run(['python3', str(ROOT/'scripts/build/stage_package.py'), name, VERSION,
                    str(stage), '--architecture', 'all', '--recipe',
                    'scripts/build/phase2/source-'+component+'-install.sh', '--depends', depends,
                    '--install'], cwd=ROOT, check=True)
    record = {'package': name, 'version': VERSION, 'component': component,
              'stage': str(stage), 'generator_manifest': manifest,
              'wrapper_sha256': digest(Path(__file__)),
              'scope': 'Native archive/install only; no activation, model, credential, grant or UI acceptance'}
    with receipt.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')


def check(component):
    name, depends, stage, receipt = paths(component)
    record = json.loads(receipt.read_text())
    assert record['wrapper_sha256'] == digest(Path(__file__))
    assert native('dpkg-query', '-W', '-f=${Status} ${Version}', name) == 'install ok installed '+VERSION
    assert not native('dpkg', '--audit')
    subprocess.run(['chroot', str(TARGET), 'apt-get', 'check'], check=True)
    checked = []
    for path in sorted(stage.rglob('*')):
        relative = path.relative_to(stage)
        if relative.parts[0] == 'DEBIAN' or (path.is_dir() and not path.is_symlink()):
            continue
        actual = TARGET/relative
        assert not path.is_symlink() and actual.is_file() and not actual.is_symlink()
        assert digest(path) == digest(actual)
        info = actual.stat()
        assert info.st_uid == info.st_gid == 0 and info.st_mode & 0o7777 == path.stat().st_mode & 0o7777
        assert native('dpkg-query', '-S', '/'+str(relative)).startswith(name+': ')
        checked.append('/'+str(relative))
    assert checked
    output = LOG/(name+'-source-package-check-1.json')
    with output.open('x') as stream:
        json.dump({'package': name, 'version': VERSION, 'checked': checked,
                   'scope': 'Actual installed bytes/modes/ownership/dependencies only; runtime acceptance pending'}, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'check'))
    parser.add_argument('component', choices=PACKAGES)
    args = parser.parse_args()
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    name = PACKAGES[args.component][0]
    transaction = json.loads((LOG.parent/'build'/('b06-source-'+args.component+'-install-1.running.json')).read_text())
    assert transaction['step'] == 'b06-source-'+args.component+'-install-1' and transaction['user'] == 'root'
    for field, suffix in [('recipe_sha256', 'install'), ('postcheck_sha256', 'check')]:
        assert transaction[field] == digest(ROOT/'scripts/build/phase2'/('source-'+args.component+'-'+suffix+'.sh'))
    if args.action == 'install':
        assert transaction['recipe_pid'] in (os.getpid(), os.getppid())
    else:
        assert transaction['recipe_exit'] == 0
    globals()[args.action](args.component)
