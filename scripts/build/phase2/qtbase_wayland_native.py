"""Fixed native QtBase6.11.2 raster upgrade preparation; coordinator invoked only."""
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

ROOT = Path('/opt/toddy-build')
TARGET = Path('/mnt/lfs')
BASE = Path('/mnt/toddy-qt-raster-1')
LOG = Path('/var/log/toddy/phase2')
SOURCE = TARGET / 'sources/phase2/inputs/qtbase-wayland-6.11.2'
WORK = TARGET / 'sources/phase2/work/qtbase-wayland-1'
STAGE = TARGET / 'sources/stage/phase2-qtbase-wayland-1'
PREPARED = LOG / 'qtbase-wayland-prepared-1.json'
VERSION = '6.11.2-1+toddy2'
OLD_VERSION = '6.11.2-1+toddy1'
SHA = '5b2e00eccaf5a4d8c14134ffa0ea8dfd0a35ae1ffc7f8d87fa4305a1ed23cf22'
ARCHIVE = 'qtbase-everywhere-src-6.11.2.tar.xz'
SCRIPTS = {'toddy-build.sh': 'qtbase-wayland-raster-build.sh',
           'toddy-qt-probe.cpp': 'qtbase-wayland-probe.cpp',
           'toddy-qt-inspect.py': 'qt_wayland_inspect.py', 'verify_stage.py': 'verify_stage.py'}
DEPENDS = ('glibc (>= 2.44-1), gcc (>= 16.2.0-1), dbus (>= 1.16.2-1), '
    'openssl (>= 4.0.3-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1), '
    'glib (>= 2.88.3-1+toddy2), systemd (>= 261.2-1), '
    'wayland (= 1.26.0-1+toddy1), libxkbcommon (= 1.13.2-1+toddy1), '
    'xkeyboard-config (= 2.48-1+toddy1), fontconfig (= 2.18.3-1+toddy1), '
    'freetype (= 2.14.3-1+toddy1), libpng (= 1.6.58-1+toddy1), '
    'libjpeg-turbo (= 3.2.0-1+toddy1), pcre2 (= 10.49-1+toddy1)')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def available(path):
    value = os.statvfs(path)
    return value.f_bavail * value.f_frsize


def save(path, value):
    part = path.with_suffix('.part')
    with part.open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    part.replace(path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def native(*args):
    return subprocess.check_output(['chroot', str(TARGET), '/usr/bin/env', '-i',
        'HOME=/root', 'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C', *args], text=True).strip()


def volume():
    assert BASE.is_dir() and not BASE.is_symlink() and BASE.resolve() == BASE
    fs, device, fsroot, mount_id, uuid = subprocess.check_output(['findmnt', '-rn', '-o',
        'FSTYPE,SOURCE,FSROOT,ID,UUID', '--mountpoint', str(BASE)], text=True).split()
    assert fs == 'ext4' and fsroot == '/' and re.fullmatch('/dev/vd[a-z]+', device)
    assert BASE.stat().st_dev != TARGET.stat().st_dev and BASE.stat().st_uid == 0
    assert BASE.stat().st_mode & 0o022 == 0
    assert subprocess.check_output(['lsblk', '-dn', '-o', 'SERIAL', device], text=True).strip() == 'TODDY-QT-RASTER-1'
    options = set(subprocess.check_output(['findmnt', '-rn', '-o', 'OPTIONS', '--mountpoint', str(BASE)], text=True).strip().split(','))
    assert {'rw', 'nosuid', 'nodev'} <= options
    return {'device': device, 'uuid': uuid, 'mount_id': mount_id,
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def package_state():
    result = {}
    for name in ('qtbase', 'qtsvg', 'qttools-linguist'):
        status, version = native('/usr/bin/dpkg-query', '-W', '-f=${Status}\t${Version}', name).split('\t')
        assert status == 'install ok installed'
        record = Path('/var/log/toddy/packages') / (name + '_' + version + '_amd64.json')
        data = json.loads(record.read_text()); assert data['installed']
        archive = Path('/var/cache/toddy/packages') / (name + '_' + version + '_amd64.deb')
        assert digest(archive) == data['archive_sha256']
        result[name] = {'version': version, 'record_sha256': digest(record),
                        'archive_sha256': data['archive_sha256']}
    return result


def bind(source, destination, readonly):
    assert not os.path.lexists(destination)
    destination.mkdir(mode=0o755)
    subprocess.run(['mount', '--bind', str(source), str(destination)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,nosuid,nodev,' + ('ro' if readonly else 'rw'), str(destination)], check=True)
    assert source.stat().st_ino == destination.stat().st_ino


def prepare():
    from source_filter import source_filter, validate_source_members
    from qt_wayland_inspect import inspect
    context = volume()
    assert available(BASE) >= 12 * 1024**3 and available(TARGET) >= 16 * 1024**3 + 64 * 1024**2
    assert not any(os.path.lexists(p) for p in (SOURCE, WORK, STAGE, PREPARED, PREPARED.with_suffix('.part'), BASE/'source', BASE/'work', BASE/'promotion'))
    before = package_state(); assert before['qtbase']['version'] == OLD_VERSION
    assert inspect(TARGET)['qtbase_rebuild_required'], 'Existing complete raster package requires no rebuild'
    row = next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name'] == 'qtbase')
    assert row['version'] == '6.11.2' and row['sha256'] == SHA and row['filename'] == ARCHIVE
    archive = TARGET/'sources'/ARCHIVE
    assert archive.is_file() and not archive.is_symlink() and digest(archive) == SHA
    state = {'state': 'prepare-intended', 'volume': context, 'source_sha256': SHA, 'before': before,
             'harness_sha256': digest(ROOT/'scripts/build/phase2/isolated.sh')}
    save(PREPARED, state)
    holder = BASE/'source'; holder.mkdir(mode=0o755)
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        assert len(members) == 26851 and sum(m.size for m in members if m.isfile()) == 276454813
        assert all(Path(m.name).parts[0] == 'qtbase-everywhere-src-6.11.2' for m in members)
        validate_source_members(ARCHIVE, members); checked = source_filter(ARCHIVE)
        for member in members:
            checked(member, holder)
        bundle.extractall(holder, filter=checked)
    source = holder/'qtbase-everywhere-src-6.11.2'
    hashes = {}
    for name, filename in SCRIPTS.items():
        assert not (source/name).exists()
        path = ROOT/'scripts/build/phase2'/filename
        (source/name).write_bytes(path.read_bytes()); (source/name).chmod(0o644)
        hashes[name] = digest(path)
    work = BASE/'work'; work.mkdir(mode=0o755); os.chown(work, 101, 101)
    bind(source, SOURCE, True); bind(work, WORK, False)
    try:
        descriptor = os.open(SOURCE/'.toddy-denial', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
        assert error.errno == errno.EROFS
    else:
        os.close(descriptor); raise AssertionError('Immutable source unexpectedly writable')
    state.update(state='prepared', scripts=hashes, source_inode=SOURCE.stat().st_ino, work_inode=WORK.stat().st_ino,
                 root_source_write_denied=True, target_free=available(TARGET), scratch_free=available(BASE))
    save(PREPARED, state)


def qualify():
    from qt_wayland_inspect import inspect
    prepared = json.loads(PREPARED.read_text()); assert prepared['state'] == 'prepared' and prepared['volume'] == volume()
    assert prepared['harness_sha256'] == digest(ROOT/'scripts/build/phase2/isolated.sh')
    for name, filename in SCRIPTS.items():
        assert digest(SOURCE/name) == prepared['scripts'][name] == digest(ROOT/'scripts/build/phase2'/filename)
    assert SOURCE.stat().st_ino == prepared['source_inode'] and WORK.stat().st_ino == prepared['work_inode']
    assert (LOG/'qtbase-wayland-1.exit').read_text().strip() == '0'
    job = json.loads((LOG/'qtbase-wayland-1.job.json').read_text())
    assert job['harness_sha256'] == prepared['harness_sha256']
    assert job['command'] == ['/bin/bash', str(ROOT/'scripts/build/phase2/isolated.sh'), str(SOURCE), str(WORK), 'bash', '/src/toddy-build.sh']
    proof = json.loads((WORK/'qt-qualified.json').read_text())
    static = inspect(WORK/'stage', stage=True)
    assert not static['qtbase_rebuild_required'] and static['stage_manifest_sha256'] == proof['stage_manifest_sha256']
    assert proof['uid'] == 101 and proof['staged_consumer_exit'] == proof['existing_lrelease_exit'] == 0
    assert proof['probe_sha256'] == prepared['scripts']['toddy-qt-probe.cpp']
    assert (WORK/'qt-staged-consumer.log').read_text().strip() == 'QT6112_WIDGET_TLS_DBUS_CONCURRENT_EXISTING_SVG_WAYLAND_METADATA_PASSED'
    return prepared, static


def elf_dependencies(stage):
    """Fail before package mutation for an unowned/undeclared direct ELF provider."""
    from audit_native_elf import target_resolve
    declared = set(re.findall(r'(?:^|,)\s*([a-z0-9][a-z0-9+.-]*)', DEPENDS))
    owners = {}
    for listing in (TARGET/'var/lib/dpkg/info').glob('*.list'):
        name = listing.name.removesuffix('.list').split(':')[0]
        for virtual in listing.read_text().splitlines():
            owners.setdefault(virtual.rstrip('/'), set()).add(name)
    checked = 0
    for path in stage.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        with path.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                continue
        checked += 1
        dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
        for kind, value in re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]', dynamic):
            if kind != 'NEEDED':
                assert value == '', 'Unexpected Qt runtime search path; retain and review'
                continue
            assert '/' not in value and value
            if (stage/'usr/lib'/value).is_file():
                continue
            provider, canonical = target_resolve(TARGET, '/usr/lib/' + value)
            assert provider.is_file(), 'Missing native provider ' + value
            found = owners.get(canonical, set()) | owners.get('/usr/lib/' + value, set())
            assert len(found) == 1 and found <= declared, 'Undeclared/ambiguous provider ' + value + ': ' + repr(found)
    assert checked > 20
    return {'elf_files': checked, 'declared_depends': DEPENDS, 'undeclared_direct_providers': 0}


def payload_bound(stage):
    # Includes new installed payload, native archive copy/output and metadata.
    # Never count on compression or removal of replaced files to meet reserve.
    total = 0
    for path in stage.rglob('*'):
        info = path.lstat()
        total += max(4096, (info.st_size + 4095) // 4096 * 4096)
    return total


def transaction(phase):
    record = json.loads((LOG.parent/'build/b12-qtbase-wayland-install.running.json').read_text())
    assert record['step'] == 'b12-qtbase-wayland-install' and record['user'] == 'root'
    assert record['recipe_sha256'] == digest(ROOT/'scripts/build/phase2/qtbase-wayland-install.sh')
    assert record['postcheck_sha256'] == digest(ROOT/'scripts/build/phase2/qtbase-wayland-check.sh')
    if phase == 'install':
        assert record['recipe_pid'] in (os.getpid(), os.getppid())
    else:
        assert phase == 'postcheck' and record['recipe_exit'] == 0


def install():
    from verify_stage import inspect_stage
    from package_copyright import write_copyright
    from dependency_preflight import native as verify_dependencies
    transaction('install')
    prepared, static = qualify()
    assert package_state() == prepared['before'], 'Accepted packages changed before transaction'
    verify_dependencies(DEPENDS)
    assert available(TARGET) >= 16 * 1024**3 + 3 * payload_bound(WORK/'stage') + 64 * 1024**2
    assert not os.path.lexists(STAGE) and not (BASE/'promotion').exists()
    destination = BASE/'promotion'
    shutil.copytree(WORK/'stage', destination, symlinks=True)
    assert inspect_stage(destination)['manifest_sha256'] == static['stage_manifest_sha256']
    closure = elf_dependencies(destination)
    bind(destination, STAGE, False)
    write_copyright(STAGE, 'qtbase', [ARCHIVE])
    required_target_bytes = 16 * 1024**3 + 3 * payload_bound(STAGE) + 64 * 1024**2
    assert available(TARGET) >= required_target_bytes, 'Verified target cache retirement required; preserve16GiB floor'
    state = {'state':'install-intended', 'version':VERSION, 'source_sha256':SHA, 'before':prepared['before'],
             'stage_manifest_sha256':static['stage_manifest_sha256'], 'closure':closure,
             'target_required_bytes':required_target_bytes}
    receipt = LOG/'qtbase-wayland-install-1.json'
    assert not receipt.exists(); save(receipt, state)
    subprocess.run([sys.executable, str(ROOT/'scripts/build/stage_package.py'), 'qtbase', VERSION, str(STAGE),
        '--source', ARCHIVE, '--recipe', 'scripts/build/phase2/qtbase-wayland-install.sh', '--depends', DEPENDS,
        '--compression-threads', '2', '--install'], cwd=ROOT, check=True)
    state.update(state='native-installed-checks-pending'); save(receipt, state)
    # run_step executes the independently named postcheck. A failure remains
    # journaled and must be reconciled; this function never retries an install.


def postcheck():
    transaction('postcheck')
    from qt_wayland_inspect import inspect
    receipt = LOG/'qtbase-wayland-install-1.json'
    state = json.loads(receipt.read_text()); assert state['state'] == 'native-installed-checks-pending'
    assert not inspect(TARGET)['qtbase_rebuild_required']
    current = package_state(); assert current['qtbase']['version'] == VERSION
    for name in ('qtsvg', 'qttools-linguist'):
        assert current[name] == state['before'][name], 'Existing Qt consumer package changed'
    for name, before in state['before'].items():
        old = name + '_' + before['version'] + '_amd64'
        assert digest(Path('/var/log/toddy/packages')/(old+'.json')) == before['record_sha256']
        assert digest(Path('/var/cache/toddy/packages')/(old+'.deb')) == before['archive_sha256']
    assert native('/usr/bin/dpkg', '--audit') == ''
    native('/usr/bin/apt-get', 'check')
    probe = TARGET/'tmp/toddy-qtbase-wayland-postcheck-1'
    assert not probe.exists(); probe.mkdir(mode=0o700)
    shutil.copyfile(ROOT/'scripts/build/phase2/qtbase-wayland-probe.cpp', probe/'probe.cpp')
    # Fixed source-controlled private offscreen test; no inherited owner bus.
    commands = r"""set -euo pipefail
cd /tmp/toddy-qtbase-wayland-postcheck-1
c++ -std=c++17 probe.cpp $(pkg-config --cflags --libs Qt6Widgets Qt6Network Qt6DBus Qt6Concurrent Qt6Svg) -o probe
QT_QPA_PLATFORM=offscreen dbus-run-session -- ./probe > consumer.log
lrelease -version > linguist.log 2>&1
if test -x /usr/bin/calamares; then
    QT_QPA_PLATFORM=offscreen calamares --version > calamares-version.log 2>&1
fi
"""
    native('/usr/bin/bash', '-c', commands)
    assert (probe/'consumer.log').read_text().strip() == 'QT6112_WIDGET_TLS_DBUS_CONCURRENT_EXISTING_SVG_WAYLAND_METADATA_PASSED'
    assert '6.11.2' in (probe/'linguist.log').read_text()
    state.update(state='native-package-and-headless-consumers-verified', installed_version=VERSION,
        old_archives_and_records_unchanged=True, existing_svg_and_linguist_unchanged=True,
        calamares_version_checked=(probe/'calamares-version.log').exists(),
        pending='Actual Wayland QWidget input/rendering, authenticated root Calamares/module launch and installer qualification')
    save(receipt, state)


def main():
    assert os.getuid() == os.geteuid() == 0 and sys.argv[1:] in (['prepare'], ['qualify'], ['install'], ['postcheck'])
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    if sys.argv[1] == 'prepare':
        with Path('/var/log/toddy/build/build.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
            prepare()
    elif sys.argv[1] == 'qualify':
        print(json.dumps(qualify()[1], indent=2))
    elif sys.argv[1] == 'postcheck':
        postcheck()
    else:
        install()


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
