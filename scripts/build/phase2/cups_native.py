"""Reviewed fixed CUPS factory identities and native promotion ownership."""
from pathlib import Path
import json
import os
import subprocess

TARGET = Path('/mnt/lfs')
OWNERS = {
    '/etc/cups': (0, 9, 0o755), '/etc/cups/ppd': (0, 9, 0o755),
    '/etc/cups/ssl': (0, 9, 0o700), '/var/cache/cups': (0, 9, 0o770),
    '/var/cache/cups/rss': (0, 9, 0o775), '/var/spool/cups': (0, 9, 0o710),
    '/var/spool/cups/tmp': (0, 9, 0o1770), '/run/cups/certs': (9, 19, 0o511),
}
for filename in ['cups-files.conf', 'cupsd.conf', 'snmp.conf']:
    for suffix in ['', '.default']:
        OWNERS['/etc/cups/' + filename + suffix] = (0, 9, 0o640)


def guard():
    assert os.geteuid() == 0
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)


def lookup(kind, name):
    result = subprocess.run(['chroot', str(TARGET), 'getent', kind, str(name)], capture_output=True, text=True)
    assert result.returncode in (0, 2)
    return result.stdout.strip().split(':') if result.returncode == 0 else None


def accounts(resume=False):
    guard()
    receipt = Path('/var/log/toddy/phase2/cups-native-accounts-'+('2' if resume else '1')+'.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Inspect existing account operation; never replay'
    defaults = dict(line.split('=',1) for line in (TARGET/'etc/default/useradd').read_text().splitlines() if line and not line.startswith('#') and '=' in line)
    assert defaults.get('CREATE_MAIL_SPOOL') == 'no'
    if resume:
        previous = json.loads(Path('/var/log/toddy/phase2/cups-native-accounts-1.json').read_text())
        assert previous['state'] == 'user-add-intended' and previous['group_created'] and not previous['user_created']
        failed = json.loads(Path('/var/log/toddy/build/b02-cups-install.failed.json').read_text())
        assert failed['recipe_exit'] == 1 and failed['postcheck_exit'] is None and failed['changed_paths'] == 4
        changes = json.loads(Path('/var/log/toddy/build/b02-cups-install.manifest.json').read_text())
        assert set(changes) == {'/etc/group','/etc/group-','/etc/gshadow','/etc/gshadow-'}
        assert lookup('passwd','lp') is None and lookup('passwd',9) is None
        assert lookup('group','lpadmin') == ['lpadmin','x','19','']
        assert not (TARGET/'sources/stage/phase2-cups').exists()
        assert not Path('/var/cache/toddy/packages/cups_2.4.19-1+toddy1_amd64.deb').exists()
    lpgroup = lookup('group', 'lp')
    assert lpgroup and lpgroup[2] == '9' and lookup('group', 9) == lpgroup
    admin = lookup('group', 'lpadmin')
    admin_id = lookup('group', 19)
    assert (admin is None and admin_id is None) or (admin == admin_id and admin[2] == '19')
    user = lookup('passwd', 'lp')
    user_id = lookup('passwd', 9)
    assert (user is None and user_id is None) or (user == user_id and user[2:4] == ['9', '9'] and user[5:] == ['/var/spool/cups', '/bin/false'])
    state = {'state': 'validated', 'uid': 9, 'gid': 9, 'admin_gid': 19,
             'group_created': False, 'user_created': False,
             'resume_verified_group_only_failure': resume,
             'scope': 'Frozen book fixed non-login print-service identity only; no owner credentials, group membership grant or service activation'}

    def save():
        part = receipt.with_suffix('.part')
        assert not part.exists()
        with part.open('x') as stream:
            stream.write(json.dumps(state, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        part.replace(receipt)

    save()
    if admin is None:
        state['state'] = 'group-add-intended'
        save()
        subprocess.run(['chroot', str(TARGET), '/usr/sbin/groupadd', '-r', '-g', '19', 'lpadmin'], check=True)
        state['group_created'] = True
        assert lookup('group', 'lpadmin')[2:] == ['19', '']
        save()
    if user is None:
        state['state'] = 'user-add-intended'
        save()
        subprocess.run(['chroot', str(TARGET), '/usr/sbin/useradd', '-r', '-M', '-N', '--no-log-init', '-u', '9', '-g', 'lp', '-d', '/var/spool/cups', '-s', '/bin/false', '-c', 'Print Service User', 'lp'], check=True)
        state['user_created'] = True
        save()
    actual = lookup('passwd', 'lp')
    assert actual[2:4] == ['9', '9'] and actual[5:] == ['/var/spool/cups', '/bin/false']
    shadow = next(line.split(':') for line in (TARGET / 'etc/shadow').read_text().splitlines() if line.startswith('lp:'))
    assert shadow[1].startswith(('!', '*')), 'Service identity must remain locked'
    if admin is not None:
        assert lookup('group', 'lpadmin') == admin
    assert lookup('group', 'lp') == lpgroup
    state.update(state='complete', locked_service_identity=True, memberships_granted=False)
    save()


def promote(stage):
    guard()
    assert stage == TARGET / 'sources/stage/phase2-cups' and stage.resolve() == stage
    for path, (uid, gid, mode) in OWNERS.items():
        file = stage / path.lstrip('/')
        assert not file.is_symlink() and file.stat().st_mode & 0o7777 == mode
    for path, (uid, gid, mode) in OWNERS.items():
        os.chown(stage / path.lstrip('/'), uid, gid)
    client = stage / 'etc/cups/client.conf'
    assert not client.exists()
    client.write_text('ServerName /run/cups/cups.sock\n')
    client.chmod(0o644)
    os.chown(client, 0, 0)
    document = stage / 'usr/share/doc/cups'
    document.mkdir(parents=True, exist_ok=True)
    (document / 'README.Toddy').write_text('Frozen CUPS2.4.19 full component profile with corrected root prefix and local IPP/unit validation. Native recipe creates locked lp UID9/GID9 and lpadmin GID19 with owned Shadow tools under the full-root transaction, following BLFS13.1 pst/cups.html. Native archives contain no maintainer scripts; a fresh external root requires these factory identity preconditions through the audited recipe before installation. No owner group membership or service activation. Source scheduler/conf/notifier ownership retained, local client socket. Remote SNMP, full printing/network/TLS/device/server/Settings GUI/hardware validation remains pending. Original wrong-prefix and resource failures retained.\n')
