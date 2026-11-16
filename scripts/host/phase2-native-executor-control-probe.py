"""Native B04 disposable integration: real system bus/systemd/Polkit and cgroups."""
import base64
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import secrets
import select
import signal
import subprocess
import time
import zlib


def run(argv, *, uid=None, timeout=30, check=True):
    kwargs = {} if uid is None else {'user': uid, 'group': uid, 'extra_groups': []}
    r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                       env={'PATH': '/usr/bin:/usr/sbin', 'LANG': 'C.UTF-8', 'HOME': '/tmp'}, **kwargs)
    if check:
        assert r.returncode == 0, ('command_failed', argv[:3], r.returncode, r.stderr[:500])
    return r


def emit(report):
    raw = json.dumps(report, sort_keys=True).encode()
    packed = base64.b64encode(zlib.compress(raw, 9)).decode()
    chunks = [packed[i:i+1024] for i in range(0, len(packed), 1024)]
    for i, part in enumerate(chunks):
        print('TODDY_B02_RUNTIME_DATA', i, part, flush=True)
    print('TODDY_B02_RUNTIME_RESULT', json.dumps({'kernel': os.uname().release,
          'all_selected_exits_zero': report['all_selected_exits_zero'],
          'report_sha256': hashlib.sha256(raw).hexdigest(), 'chunks': len(chunks)}), flush=True)


def main():
    assert os.geteuid() == 0 and os.uname().release == '7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip() == 'systemd'
    assert run(['systemd-detect-virt', '--vm']).stdout.strip() in ('kvm', 'qemu')
    device = run(['findmnt', '-n', '-o', 'SOURCE', '/']).stdout.strip()
    assert re.fullmatch('/dev/[a-z0-9]+', device)
    parent = run(['lsblk', '-ndo', 'PKNAME', device]).stdout.strip()
    assert re.fullmatch('[a-z0-9]+', parent)
    assert run(['lsblk', '-dnro', 'SERIAL', '/dev/'+parent]).stdout.strip() == 'TODDY-BOOT-TEST'
    assert run(['findmnt', '-n', '-o', 'FSTYPE', '/sys/fs/cgroup']).stdout.strip() == 'cgroup2'
    credentials = Path(os.environ['CREDENTIALS_DIRECTORY'])
    manifest = json.loads((credentials/'toddy.executor.manifest').read_text())
    packed = b''.join((credentials/('toddy.executor.input'+str(i))).read_bytes() for i in range(manifest['chunks']))
    assert hashlib.sha256(packed).hexdigest() == manifest['sha256']
    files = json.loads(zlib.decompress(packed))
    root = Path('/usr/lib/toddy/executor')
    assert not root.exists(), 'Do not overlay an existing installed executor'
    root.mkdir(parents=True, mode=0o755)
    hashes = {}
    for name, text in files.items():
        assert name == Path(name).name and name.endswith(('.py', '.xml'))
        target = root/name; target.write_text(text); target.chmod(0o755 if name == 'owner_policy.py' else 0o644)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    for name, destination in manifest['packaging'].items():
        path = Path(destination['path']); assert str(path).startswith(('/etc/dbus-1/', '/etc/systemd/', '/usr/share/polkit-1/'))
        assert not path.exists(), 'Do not replace existing product policy'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(destination['text']); path.chmod(0o644)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    Path('/var/lib/toddy').mkdir(mode=0o755, exist_ok=True)
    run(['dbus-send', '--system', '--type=method_call', '--print-reply', '--dest=org.freedesktop.DBus', '/', 'org.freedesktop.DBus.ReloadConfig'])
    unit = Path('/etc/systemd/system/toddy-executor-test.service')
    unit.write_text('[Service]\nType=simple\nExecStart=/usr/bin/sleep infinity\n')
    run(['systemctl', 'daemon-reload'])
    run(['systemctl', 'start', 'polkit.service', 'NetworkManager.service', 'toddy-executor.service'])
    assert run(['systemctl', 'is-active', 'toddy-executor.service']).stdout.strip() == 'active'
    uid = 12404; username = 'toddy-executor-owner'
    run(['useradd', '-m', '-U', '-u', str(uid), '-s', '/bin/bash', username])
    secret = secrets.token_urlsafe(32)
    changed = subprocess.run(['chpasswd', '-c', 'YESCRYPT'], input=username+':'+secret+'\n', text=True, capture_output=True, timeout=15)
    assert changed.returncode == 0, 'Ephemeral credential setup failed'
    Path('/etc/pam.d/polkit-auth').write_text('auth required pam_unix.so\naccount required pam_unix.so\nsession required pam_unix.so\n')
    report = {'scope': 'Disposable B04 native systemd/system-bus/cgroup/structured-service/network/fixed-owner-helper integration; inactive test subject gets an explicit fixture challenge rule. Active GNOME default-policy/session-grant and installed package lifecycle still pending. No G2/physical acceptance.',
              'all_selected_exits_zero': False, 'source_sha256': hashes, 'checks': []}
    def passed(name, **values):
        report['checks'].append({'name': name, **values}); print('TODDY_B04_STAGE', name, flush=True)
    client = Path('/tmp/toddy-executor-client.py')
    client.write_text('''import gi,json,sys
from gi.repository import Gio,GLib
c=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
method=sys.argv[1];values=json.loads(sys.argv[2]);sig='(sss)' if len(values)==3 else '(s)'
try:
 r=c.call_sync('io.github.markaraujo.Toddy.Executor','/io/github/markaraujo/Toddy/Executor','io.github.markaraujo.Toddy.Executor1',method,GLib.Variant(sig,tuple(values)),GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,90000,None)
 print(r.unpack()[0])
except GLib.Error as e:
 print(e.message);sys.exit(2)
'''); client.chmod(0o644)
    def call(method, values, *, caller=uid, expect=True):
        r = run(['/usr/bin/python3', str(client), method, json.dumps(values)], uid=caller, timeout=95, check=False)
        if expect:
            assert r.returncode == 0, ('ipc_failed', method, r.stdout[:400], r.stderr[:300])
            return json.loads(r.stdout)
        assert r.returncode != 0, ('expected_ipc_refusal', method)
        return r.stdout
    def operation(name, kind, args):
        values = [name, kind, json.dumps(args)]
        assert call('PlanOperation', values)['state'] == 'planned'
        result = call('DispatchOperation', values)
        assert result['state'] == 'completed' and result['result']['verified']
        return result
    helper = str(root/'owner_policy.py')
    r = run([helper, 'grant', '--mode', 'standing', '--expires-in', '3600'], uid=uid, check=False)
    assert r.returncode and not Path('/var/lib/toddy/executor/state.sqlite').stat().st_mode & 0o077
    call('PlanOperation', ['no-grant', 'network_operation', '{"enabled":true}'], expect=False)
    passed('direct-unprivileged-helper-and-ungranted-ipc-refused')
    # This headless subject has no active local session: production default denies.
    denied = run(['/usr/bin/pkexec', '--disable-internal-agent', helper, 'audit'], uid=uid, check=False)
    assert denied.returncode != 0
    passed('inactive-default-policy-refused')
    rules = Path('/etc/polkit-1/rules.d/00-toddy-executor-fixture.rules')
    rules.write_text('polkit.addAdminRule(function(a,s){if(a.id=="io.github.markaraujo.Toddy.owner-policy")return ["unix-user:'+username+'"];});\npolkit.addRule(function(a,s){if(a.id=="io.github.markaraujo.Toddy.owner-policy" && s.user=="'+username+'")return polkit.Result.AUTH_ADMIN;});\n')
    run(['systemctl', 'restart', 'polkit.service'])
    def authenticate(action, password, *, success=True, cancel=False):
        argv = ['/usr/bin/pkexec', helper, action]
        if action == 'grant': argv += ['--mode', 'standing', '--expires-in', '3600']
        pid, fd = pty.fork()
        if pid == 0:
            os.setgroups([]); os.setgid(uid); os.setuid(uid)
            os.environ.clear(); os.environ.update(PATH='/usr/bin:/usr/sbin', LANG='C.UTF-8', HOME='/tmp', TERM='dumb')
            os.execv(argv[0], argv)
        transcript=b'';tail=b'';prompts=0;status=None;deadline=time.monotonic()+35
        try:
            while time.monotonic() < deadline:
                if select.select([fd], [], [], .1)[0]:
                    try: data=os.read(fd, 8192)
                    except OSError: data=b''
                    transcript+=data;tail=(tail+data)[-4096:]
                    assert len(transcript)<65536
                    if re.search(rb'[Pp]assword: *$', tail):
                        prompts+=1;tail=b''
                        if cancel: os.kill(pid, signal.SIGINT)
                        else: os.write(fd,password.encode()+b'\n')
                waited, raw=os.waitpid(pid, os.WNOHANG)
                if waited: status=os.waitstatus_to_exitcode(raw);break
            if status is None:
                os.kill(pid, signal.SIGKILL);os.waitpid(pid,0)
                raise AssertionError('owner_authentication_deadline')
            assert prompts > 0 and ((status == 0) == success), ('owner_authentication_result', action, status, prompts)
            passed('owner-auth-'+action+('-cancel' if cancel else '-success' if success else '-wrong-password'), exit=status, prompts=prompts, raw_tty_retained=False)
        finally: os.close(fd)
    authenticate('grant', secrets.token_urlsafe(32), success=False)
    call('PlanOperation', ['still-no-grant', 'network_operation', '{"enabled":true}'], expect=False)
    authenticate('grant', secret, success=False, cancel=True)
    call('PlanOperation', ['cancel-no-grant', 'network_operation', '{"enabled":true}'], expect=False)
    authenticate('grant', secret)
    a=operation('service-start', 'service_operation', {'action':'start','unit':unit.name})
    b=operation('service-stop', 'service_operation', {'action':'stop','unit':unit.name})
    assert a['result']['active_state']=='active' and b['result']['active_state']=='inactive'
    passed('authenticated-service-start-stop-native-postconditions')
    operation('network-off','network_operation',{'enabled':False})
    operation('network-on','network_operation',{'enabled':True})
    passed('authenticated-network-off-on-native-postconditions')
    args={'path':'/etc/toddy-executor-proof.conf','text':'owner-authorized\n','expected_sha256':None}
    operation('config-write','config_replace',args)
    duplicate=call('DispatchOperation',['config-write','config_replace',json.dumps(args)])
    assert duplicate['state']=='completed' and Path(args['path']).read_text()==args['text']
    assert call('GetOperation',['config-write'],caller=65534,expect=False)
    passed('root-config-postcondition-duplicate-no-replay-wrong-user-denial')
    planned=['revoked-operation','network_operation','{"enabled":false}']
    call('PlanOperation',planned)
    authenticate('revoke',secret)
    call('DispatchOperation',planned,expect=False)
    assert run(['nmcli','--terse','networking']).stdout.strip()=='enabled'
    passed('authenticated-revoke-blocks-previous-plan')
    authenticate('grant',secret)
    # A detached descendant escapes process-group/pdeath, but not systemd cgroup.
    childpid=Path('/tmp/toddy-detached.pid'); marker=Path('/tmp/toddy-effect-once')
    code='import os,time;from pathlib import Path;p=os.fork();\nif p==0:\n os.setsid();Path("/tmp/toddy-detached.pid").write_text(str(os.getpid()));time.sleep(90)\nelse:\n Path("/tmp/toddy-effect-once").write_text("once");time.sleep(90)'
    args={'argv':['/usr/bin/python3','-c',code],'timeout_seconds':120,'acknowledge_unrestricted_root':True}
    values=['cgroup-loss','root_command',json.dumps(args)]
    call('PlanOperation',values)
    active=subprocess.Popen(['/usr/bin/python3',str(client),'DispatchOperation',json.dumps(values)],user=uid,group=uid,extra_groups=[],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    until=time.monotonic()+10
    while time.monotonic()<until and not childpid.exists():time.sleep(.1)
    assert childpid.exists() and marker.read_text()=='once'
    descendant=int(childpid.read_text()); cgroup=run(['systemctl','show','toddy-executor.service','-p','ControlGroup','--value']).stdout.strip()
    assert cgroup and cgroup in Path('/proc',str(descendant),'cgroup').read_text()
    run(['systemctl','stop','toddy-executor.service'],timeout=25)
    active.communicate(timeout=10)
    assert not Path('/proc',str(descendant)).exists(), 'Detached descendant survived cgroup stop'
    run(['systemctl','start','toddy-executor.service'])
    recovered=call('GetOperation',['cgroup-loss']);assert recovered['state']=='uncertain'
    again=call('DispatchOperation',values);assert again['state']=='uncertain' and marker.read_text()=='once'
    passed('actual-systemd-cgroup-detached-child-stop-and-uncertain-no-replay')
    authenticate('revoke',secret)
    audit=run(['/usr/bin/python3',str(root/'policy.py'),'audit','--uid',str(uid)]).stdout
    assert secret not in audit and 'owner-authorized' not in audit and 'acknowledge_unrestricted_root' not in audit
    passed('audit-excludes-credential-arguments-and-config-content')
    secret=None
    run(['systemctl','stop','toddy-executor.service','toddy-executor-test.service'])
    rules.unlink();run(['systemctl','restart','polkit.service'])
    run(['userdel','-r',username])
    report['all_selected_exits_zero']=True
    emit(report)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        emit({'all_selected_exits_zero':False,'error_type':type(error).__name__,'error':str(error)})
        raise
