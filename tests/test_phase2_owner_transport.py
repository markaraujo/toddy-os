"""Exercise private socket transport and ensure fixture passwords never enter logs."""
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
import phase2_gdm_owner_control as control


class OwnerTransportTest(unittest.TestCase):
    def test_password_only_in_memory_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            context=Path(temporary)
            auth=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            auth.bind(str(context/'auth'));auth.listen(1)
            qmp=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            qmp.bind(str(context/'q'));qmp.listen(1)
            received=[];keys=[];errors=[];stop=threading.Event()
            def guest():
                try:
                    with auth.accept()[0] as connection:
                        connection.settimeout(10)
                        stream=connection.makefile('rwb',buffering=0)
                        stream.write(b'READY\n');received.append(stream.readline().strip())
                        stream.write(b'CONFIGURED\n')
                        self.assertEqual(stream.readline(),b'DONE\n')
                except Exception as error:errors.append(error)
            def machine():
                try:
                    with qmp.accept()[0] as connection:
                        connection.settimeout(10);stream=connection.makefile('rwb',buffering=0)
                        stream.write(b'{"QMP":{}}\n')
                        while line:=stream.readline():
                            request=json.loads(line)
                            if request['execute']=='send-key':keys.append(request['arguments']['keys'][0]['data'])
                            stream.write(b'{"return":{}}\n')
                except Exception as error:errors.append(error)
            threads=[threading.Thread(target=f,daemon=True) for f in [guest,machine]]
            worker=threading.Thread(target=control.run,args=(context,stop),daemon=True)
            for thread in threads+[worker]:thread.start()
            deadline=time.monotonic()+10
            while not (context/'control').exists():
                self.assertLess(time.monotonic(),deadline)
                time.sleep(.01)
            for action in ['password','done']:
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                    client.settimeout(10);client.connect(str(context/'control'))
                    client.sendall(json.dumps({'action':action}).encode())
                    reply=json.loads(client.recv(4096));self.assertTrue(reply)
            stop.set();worker.join(10)
            for thread in threads:thread.join(10)
            auth.close();qmp.close()
            self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
            self.assertEqual(len(received[0]),24)
            self.assertEqual(''.join(keys).encode(),received[0])
            for path in context.glob('*.json'):
                self.assertNotIn(received[0].decode(),path.read_text())


if __name__=='__main__':unittest.main()
