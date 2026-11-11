"""Validate installed Settings payload and native CLI without claiming GUI coverage."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from qualify_control_center import LOG, digest, qualify

TARGET = Path('/mnt/lfs')


def main():
    entries, _ = qualify()
    chroot = ['chroot', str(TARGET)]
    assert subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'gnome-control-center'], text=True) == 'install ok installed 50.4-1+toddy1'
    assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
    subprocess.run(chroot + ['apt-get', 'check'], check=True)
    for relative, row in entries.items():
        path = TARGET / relative
        if 'sha256' in row:
            assert digest(path) == row['sha256']
        if 'symlink' in row:
            assert path.readlink() == Path(row['symlink'])
    notices = TARGET / 'usr/share/doc/gnome-control-center/source-notices'
    index = json.loads((notices / 'index.json').read_text())
    assert len(index['sources']) == 2
    assert all(digest(notices / notice['sha256']) == notice['sha256']
               for source in index['sources'] for notice in source['notices'])
    wrapper = '''
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev
for name in null zero random urandom; do
 touch "/mnt/lfs/dev/$name"
 mount --bind "/dev/$name" "/mnt/lfs/dev/$name"
done
mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc
exec setpriv --no-new-privs chroot --userspec=101:101 /mnt/lfs python3 -c "$1"
'''
    consumer = '''
import json, os, subprocess
from pathlib import Path
assert os.getuid() == os.geteuid() == 101
status = Path('/proc/self/status').read_text()
assert 'CapEff:\\t0000000000000000' in status and 'NoNewPrivs:\\t1' in status
version = subprocess.check_output(['gnome-control-center', '--version'], text=True)
assert version.strip() == 'Local options gnome-control-center 50.4'
env = dict(os.environ, XDG_CURRENT_DESKTOP='GNOME')
original = subprocess.check_output(['gnome-control-center', '--list'], env=env, text=True)
panels = [line.strip() for line in original.splitlines()[1:] if line.strip()]
assert len(panels) == 23 and {'system','network','printers','display','sound','keyboard'} <= set(panels)
refused = subprocess.run(['gnome-control-center', '--toddy-invalid-option'], capture_output=True, text=True)
assert refused.returncode != 0
assert subprocess.check_output(['gnome-control-center', '--list'], env=env, text=True) == original
for path in ('/usr/bin/gnome-control-center', '/usr/libexec/gnome-control-center-search-provider',
             '/usr/libexec/gnome-control-center-global-shortcuts-provider','/usr/libexec/gnome-control-center-print-renderer'):
    linkage = subprocess.check_output(['ldd', path], text=True)
    assert 'not found' not in linkage and '/build/' not in linkage and '/src/' not in linkage
private = Path(os.environ['HOME'])
subprocess.run(['glib-compile-schemas','--strict',str(private)],check=True)
from gi.repository import Gio
source = Gio.SettingsSchemaSource.new_from_directory(str(private), Gio.SettingsSchemaSource.get_default(), False)
schema = source.lookup('org.gnome.Settings', False)
assert schema and set(schema.list_keys()) == {'last-panel','show-development-warning','window-state'}
assert schema.get_key('last-panel').get_default_value().unpack() == ''
assert schema.get_key('show-development-warning').get_default_value().unpack() is True
assert schema.get_key('window-state').get_default_value().unpack() == (-1,-1,False)
print(json.dumps({'version':'50.4','uid':101,'compiled_panels':panels,'invalid_option_refused':True,
                  'list_recovery_identical':True,'native_executable_linkage_count':4,'private_schema_defaults':3}))
'''
    env = {'PATH':'/usr/bin:/usr/sbin', 'LC_ALL':'C.UTF-8', 'GTK_A11Y':'none',
           'PYTHONDONTWRITEBYTECODE':'1', 'PYTHONNOUSERSITE':'1'}
    with tempfile.TemporaryDirectory(prefix='toddy-settings-', dir=TARGET / 'tmp') as directory:
        temp = Path(directory)
        os.chown(temp, 101, 101)
        env['HOME'] = '/tmp/' + temp.name
        shutil.copyfile(TARGET / 'usr/share/glib-2.0/schemas/org.gnome.Settings.gschema.xml', temp / 'org.gnome.Settings.gschema.xml')
        actual = subprocess.check_output(['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,
                                         'toddy-settings',consumer], env=env, text=True, timeout=30)
    result = json.loads(actual)
    assert result['private_schema_defaults'] == 3
    space = os.statvfs(TARGET)
    assert space.f_bavail * space.f_frsize >= 16 * 1024**3
    result.update(notice_count=sum(len(source['notices']) for source in index['sources']),
                  scope='Installed Settings CLI, payload, native linkage and private schema defaults. Shared system schema-cache integration and graphical actions pending.')
    (LOG / 'gnome-control-center-installed-consumer.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
