"""Private QMP input control; synthetic fixture password stays in process memory."""
import json
import os
from pathlib import Path
import secrets
import resource
import socket
import string
import time


def connect(path, stop, deadline):
    while not path.exists():
        assert time.monotonic() < deadline, 'Private transport not ready'
        if stop.wait(.25):
            raise InterruptedError('Native controller stopped')
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect(str(path))
    return s


def run(context, stop):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    events = []
    private = None
    qmp = None
    listener = None
    credential = None
    try:
        deadline = time.monotonic() + 120
        private = connect(context/'auth', stop, deadline)
        private.settimeout(120)
        transport = private.makefile('rwb', buffering=0)
        assert transport.readline(64) == b'READY\n'
        credential = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(24))
        transport.write(credential.encode()+b'\n')
        assert transport.readline(64) == b'CONFIGURED\n'
        qmp = connect(context/'q', stop, deadline)
        stream = qmp.makefile('rwb', buffering=0)
        assert 'QMP' in json.loads(stream.readline())
        def call(name, arguments=None):
            stream.write((json.dumps({'execute':name, **({'arguments':arguments} if arguments else {})})+'\n').encode())
            while True:
                result = json.loads(stream.readline())
                if 'event' in result:
                    continue
                assert 'return' in result, 'QMP operation refused'
                return result['return']
        call('qmp_capabilities')
        def key(code):
            call('send-key', {'keys':[{'type':'qcode','data':code}], 'hold-time':60})
            time.sleep(.10)
        def text(value):
            for char in value:
                assert char in string.ascii_lowercase+string.digits+'-'
                key('minus' if char=='-' else char)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(context/'control'))
        os.chmod(context/'control', 0o600)
        listener.listen(1)
        listener.settimeout(1)
        events.append({'phase':'private-account-configured-control-ready'})
        (context/'control-ready.json').write_text(json.dumps(events[-1])+'\n')
        index = 0
        while not stop.is_set():
            try:
                client, _ = listener.accept()
            except socket.timeout:
                continue
            with client:
                client.settimeout(10)
                request = json.loads(client.recv(4096))
                action = request['action']
                if action == 'capture':
                    name = 'owner-scanout-%02d.ppm' % index
                    index += 1
                    call('screendump', {'filename':'/work/'+name})
                    reply = {'frame':name}
                elif action == 'username':
                    text('toddy-preview')
                    reply = {'username_sent':True}
                elif action == 'password':
                    text(credential)
                    reply = {'private_password_sent':True}
                elif action == 'text':
                    value = request['text']
                    assert len(value)<=80 and all(c in string.ascii_lowercase+string.digits+'-' for c in value)
                    text(value)
                    reply = {'text_sent':True}
                elif action == 'key':
                    codes = request['codes']
                    assert 1<=len(codes)<=3 and all(c in ['ret','esc','tab','spc','backspace','up','down','left','right','home','end','ctrl','alt','shift','meta_l','f4','a','s','o','q','n','v','t','minus','equal'] for c in codes)
                    call('send-key', {'keys':[{'type':'qcode','data':c} for c in codes], 'hold-time':80})
                    reply = {'key_sent':True}
                elif action == 'pointer':
                    x,y = request['x'],request['y']
                    assert 0<=x<=32767 and 0<=y<=32767
                    call('input-send-event', {'events':[{'type':'abs','data':{'axis':'x','value':x}},{'type':'abs','data':{'axis':'y','value':y}}]})
                    if request.get('click'):
                        call('input-send-event', {'events':[{'type':'btn','data':{'button':'left','down':True}}]})
                        call('input-send-event', {'events':[{'type':'btn','data':{'button':'left','down':False}}]})
                    reply = {'pointer_sent':True}
                elif action == 'done':
                    transport.write(b'DONE\n')
                    reply = {'guest_observation_finish_requested':True}
                else:
                    raise AssertionError('Unsupported control action')
                events.append({'action':action,'result':reply,'monotonic':time.monotonic()})
                (context/'owner-input-events.json').write_text(json.dumps(events,indent=2)+'\n')
                client.sendall(json.dumps(reply).encode())
    except Exception as error:
        events.append({'error':type(error).__name__, 'message':'Private native input control stopped; inspect terminal native evidence and retained frames.'})
    finally:
        credential = None
        for connection in [listener,qmp,private]:
            if connection:
                connection.close()
        (context/'owner-input-events.json').write_text(json.dumps(events,indent=2)+'\n')
