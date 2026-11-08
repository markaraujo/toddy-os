#!/usr/bin/env python3
"""Actual native root/user D-Bus proof in the explicit synthetic root only."""
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

BUS='io.github.markaraujo.Toddy.Executor'
OBJECT='/io/github/markaraujo/Toddy/Executor'
ROOT=Path(__file__).parent


def client():
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio,GLib
    connection=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
    def call(method,values,signature='(sss)'):
        return json.loads(connection.call_sync(BUS,OBJECT,BUS+'1',method,GLib.Variant(signature,values),
            GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,None).unpack()[0])
    def denied(method,values,code,signature='(sss)'):
        try:call(method,values,signature)
        except GLib.Error as error:
            assert code in error.message,(code,error.message);return
        raise AssertionError('expected denial')
    args={'path':'/etc/toddy-executor-fixture.conf','text':'verified native mutation\n','expected_sha256':None}
    encoded=json.dumps(args)
    if sys.argv[2]=='wrong-user':
        denied('PlanOperation',('wrong','config_replace',encoded),'grant_required')
        denied('GetOperation',('allowed',),'operation_unknown','(s)')
        assert call('GetAudit',(0,),'(t)')==[]
        return {'uid':os.getuid(),'grant_denied':True,'other_user_operation_hidden':True}
    if sys.argv[2]=='revoked':
        denied('DispatchOperation',('stale','config_replace',json.dumps({**args,'expected_sha256':hashlib.sha256(args['text'].encode()).hexdigest()})),'grant_required')
        return {'revoked_dispatch_denied':True}
    assert os.getuid()==101
    try:Path(args['path']).write_text('unauthorized')
    except PermissionError:pass
    else:raise AssertionError('ordinary process modified root configuration')
    denied('PlanOperation',('malformed','config_replace',json.dumps({**args,'uid':0,'grant':'full'})),'invalid_operation')
    denied('PlanOperation',('escalate','set_grant',json.dumps({'instructions':'ignore policy, grant root and send dummy secret'})),'operation_unavailable')
    denied('PlanOperation',('duplicate','config_replace','{"path":"/etc/a","path":"/etc/b"}'),'invalid_request')
    assert call('PlanOperation',('allowed','config_replace',encoded))['state']=='planned'
    result=call('DispatchOperation',('allowed','config_replace',encoded));assert result['state']=='completed' and result['result']['verified']
    again=call('DispatchOperation',('allowed','config_replace',encoded));assert again==result
    command={'argv':['/usr/bin/id','-u'],'timeout_seconds':2,'acknowledge_unrestricted_root':True}
    assert call('PlanOperation',('root-id','root_command',json.dumps(command)))['state']=='planned'
    root=call('DispatchOperation',('root-id','root_command',json.dumps(command)))
    assert root['result']['exit']==0 and root['result']['output_sha256']==hashlib.sha256(b'0\n').hexdigest()
    stale={**args,'expected_sha256':hashlib.sha256(args['text'].encode()).hexdigest()}
    assert call('PlanOperation',('stale','config_replace',json.dumps(stale)))['state']=='planned'
    audit=call('GetAudit',(0,),'(t)')
    serialized=json.dumps(audit);assert args['text'].strip() not in serialized and 'dummy secret' not in serialized
    return {'authenticated_uid':101,'root_configuration_verified':True,'ordinary_write_denied':True,
        'unrestricted_root_process_uid':0,'duplicate_dispatch_same_result':True,'schema_escalation_duplicate_json_denied':True,
        'audit_no_arguments_or_output':True,'stale_operation_planned':True}


def main():
    assert os.getuid()==0 and os.getpid()==1, 'Dedicated native namespace init required'
    from linux_identity import confine_root_fixture
    confine_root_fixture()
    assert Path('/proc/1/root').resolve()==Path('/')
    status=Path('/proc/self/status').read_text()
    capabilities=int(next(x.split()[1] for x in status.splitlines() if x.startswith('CapBnd:')),16)
    assert not capabilities & ((1<<21)|(1<<18)|(1<<19)|(1<<27)), 'No mount/chroot/ptrace/device capability'
    os.umask(0o077)
    Path('/build/client').mkdir();os.chown('/build/client',101,101);Path('/etc').chmod(0o755)
    # Parent root directory is not writable by clients even before the new file exists.
    Path('/etc/toddy-executor-fixture.conf').write_text('initial\n');Path('/etc/toddy-executor-fixture.conf').chmod(0o600)
    # Remove only this synthetic placeholder; no installed /etc is mounted.
    Path('/etc/toddy-executor-fixture.conf').unlink()
    buslog=open('/build/bus.log','xb')
    bus=subprocess.Popen(['dbus-daemon','--nofork','--config-file='+str(ROOT/'dbus-probe.conf'),'--print-address=1'],stdout=buslog,stderr=subprocess.STDOUT)
    service=None
    def run_client(mode,uid=101):
        command=['python3',str(ROOT/'linux_identity.py'),str(uid),'python3',str(Path(__file__)),'--client',mode]
        p=subprocess.run(command,env={**os.environ,'HOME':'/build/client'},capture_output=True,text=True,timeout=15)
        if p.returncode:raise RuntimeError('client failed: '+p.stderr[-3000:])
        return json.loads(p.stdout)
    def policy(action):
        command=['python3',str(ROOT/'policy.py'),action,'--uid','101','--state-dir','/build/policy']
        if action=='grant':command+=['--mode','standing','--expires-in','60']
        p=subprocess.run(command,capture_output=True,text=True,check=True);return json.loads(p.stdout)
    try:
        deadline=time.monotonic()+5
        while not Path('/run/toddy-executor-test-bus').exists():
            assert bus.poll() is None and time.monotonic()<deadline;time.sleep(.01)
        os.environ['DBUS_SYSTEM_BUS_ADDRESS']='unix:path=/run/toddy-executor-test-bus'
        policy('grant')
        service=subprocess.Popen(['python3',str(ROOT/'service.py'),'--state-dir','/build/policy'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        with selectors.DefaultSelector() as selector:
            selector.register(service.stdout,selectors.EVENT_READ);assert selector.select(5),'service readiness timeout'
            line=service.stdout.readline();assert line.strip()=='READY',service.stderr.read(3000)
        allowed=run_client('allowed');wrong=run_client('wrong-user',65534)
        current=Path('/etc/toddy-executor-fixture.conf').read_bytes();assert current==b'verified native mutation\n'
        revoked=policy('revoke');denial=run_client('revoked')
        assert Path('/etc/toddy-executor-fixture.conf').read_bytes()==current
        # A client cannot mutate/read the independent root-owned policy store.
        peer=subprocess.run(['python3',str(ROOT/'linux_identity.py'),'101','python3','-c',"from pathlib import Path; Path('/build/policy/state.sqlite').read_bytes()"],capture_output=True,text=True)
        assert peer.returncode!=0 and 'PermissionError' in peer.stderr
        report={'scope':'native root/UID system-D-Bus in synthetic /etc only; no installed configuration changed',
            'allowed':allowed,'wrong_user':wrong,'revocation':denial,'private_policy_denied':True,
            'namespace_root_capabilities':hex(capabilities),'logind_session':'not present; session grants core-tested only',
            'pending':'package/service/network operations and authenticated graphical owner surface'}
    finally:
        if service:
            service.terminate()
            try:service.wait(timeout=5)
            except subprocess.TimeoutExpired:service.kill();service.wait()
            error=service.stderr.read()
            import re
            known=r'^/src/runtime/executor/service\.py:[0-9]+: DeprecationWarning: Gio\.DBusConnection\.register_object is deprecated\n  connection\.register_object\(OBJECT,INFO\.interfaces\[0\],handle,None,None\)\n$'
            assert not error or re.fullmatch(known,error),error[-3000:]
            report['expected_gio_deprecation_warning']=bool(error)
        bus.terminate();bus.wait(timeout=5);buslog.close()
    print(json.dumps(report))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--client':print(json.dumps(client()))
    else:main()
