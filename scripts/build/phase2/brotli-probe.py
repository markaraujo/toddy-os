"""Lossless CLI binary/UTF8 roundtrip, integrity refusal and recovery."""
from pathlib import Path
import hashlib,json,subprocess,sys
binary=sys.argv[1];root=Path(sys.argv[2]);root.mkdir()
assert '1.2.0' in subprocess.check_output([binary,'--version'],text=True,stderr=subprocess.STDOUT)
for cycle in range(2):
 plain=root/('plain-'+str(cycle));encoded=root/('encoded-'+str(cycle)+'.br');out=root/('restored-'+str(cycle));data=('Olá Toddy\n'*64).encode()+bytes(range(256))*4;plain.write_bytes(data)
 subprocess.run([binary,'-o',str(encoded),str(plain)],check=True,capture_output=True)
 subprocess.run([binary,'--test',str(encoded)],check=True,capture_output=True)
 subprocess.run([binary,'--decompress','-o',str(out),str(encoded)],check=True,capture_output=True)
 assert out.read_bytes()==plain.read_bytes()==data
 bad=root/('bad-'+str(cycle)+'.br');bad.write_bytes(b'\xff\xff\xff\xff');before=bad.read_bytes();refused=root/('refused-'+str(cycle));r=subprocess.run([binary,'--decompress','-o',str(refused),str(bad)],capture_output=True)
 assert r.returncode!=0 and bad.read_bytes()==before
 # Recovery uses a new destination and the retained valid compressed input.
 recovered=root/('recovery-'+str(cycle));subprocess.run([binary,'--decompress','-o',str(recovered),str(encoded)],check=True,capture_output=True);assert recovered.read_bytes()==data
print(json.dumps({'UTF8_and_binary_roundtrip_cycles':2,'compressed_integrity_checks':2,'malformed_refusals':2,'malformed_input_unchanged':True,'recovery_cycles':2}))
