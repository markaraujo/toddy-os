#!/usr/bin/env python3
"""Classify six exact native OpenSSL manual examples without suppressing findings."""
import hashlib
import json
from pathlib import Path
import subprocess
from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]
REMOTE = r'''
import base64,binascii,hashlib,json,re,subprocess,sys,tarfile
from html.parser import HTMLParser
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
from locked_inputs import locked_source
root=Path('/mnt/lfs');backend=PackageBackend(root)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
version,arch,state=backend.run('dpkg-query','-W','-f=${Version}\t${Architecture}\t${Status}','openssl',capture_output=True,text=True).stdout.split('\t')
assert state=='install ok installed'
record_path=Path('/var/log/toddy/packages')/f'openssl_{version}_{arch}.json'
record=json.loads(record_path.read_text());assert record['installed']
package=Path('/var/cache/toddy/packages')/f'openssl_{version}_{arch}.deb'
assert digest(package)==record['archive_sha256']
source=root/'sources/openssl-4.0.3.tar.gz'
assert digest(source)==locked_source(Path('/opt/toddy-build'),source.name)['sha256']
assert digest(root/'usr/bin/openssl')==record['payload']['/usr/bin/openssl']['sha256']
native_version=backend.run('openssl','version',capture_output=True,text=True).stdout.strip()
assert native_version.startswith('OpenSSL 4.0.3 '),native_version
pattern=re.compile(r'-----BEGIN (?P<label>(?:RSA |DSA |EC |ENCRYPTED )?PRIVATE KEY)-----(?P<body>.*?)-----END (?P=label)-----',re.S)
header=re.compile(r'-----BEGIN (?:(?:RSA |DSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY|PGP PRIVATE KEY BLOCK)-----')
def normalize(text):return '\n'.join(line.strip() for line in text.strip().splitlines())+'\n'
class Text(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
 def handle_data(self,data):self.parts.append(data)
rows=[]
with tarfile.open(source) as archive:
 for relative in ('man3/PEM_read','man3/PEM_read_bio_PrivateKey','man7/openssl-glossary'):
  name='openssl-4.0.3/doc/'+relative+'.pod'
  original=archive.extractfile(name).read();text=original.decode()
  examples=list(pattern.finditer(text));assert len(examples)==len(header.findall(text))==1
  example=normalize(examples[0].group(0))
  body=''.join(line.strip() for line in examples[0]['body'].splitlines()
               if line.strip() and not line.strip().startswith(('Proc-Type:','DEK-Info:')))
  assert '...' in body
  try:base64.b64decode(body,validate=True)
  except binascii.Error:pass
  else:raise AssertionError('Documentation contains decodable key-shaped data')
  result=subprocess.run(['chroot',str(root),'/usr/bin/openssl','pkey','-noout','-check','-passin','pass:'],
   input=example.encode(),capture_output=True,timeout=10)
  assert result.returncode==1 and not result.stdout,'Native parser unexpectedly accepted the example'
  for suffix in (relative+'.pod','html/'+relative+'.html'):
   virtual='/usr/share/doc/openssl-4.0.3/'+suffix;path=root/virtual[1:]
   assert path.resolve()==path and digest(path)==record['payload'][virtual]['sha256']
   content=path.read_text()
   if suffix.endswith('.pod'):assert path.read_bytes()==original
   else:
    parser=Text();parser.feed(content);content=''.join(parser.parts)
   found=list(pattern.finditer(content));assert len(found)==len(header.findall(content))==1
   assert normalize(found[0].group(0))==example
   rows.append({'path':virtual,'sha256':digest(path),'frozen_source_document':name,
    'source_document_sha256':hashlib.sha256(original).hexdigest(),
    'normalized_example_sha256':hashlib.sha256(example.encode()).hexdigest(),
    'classification':'Exact frozen manual format placeholder; not key material',
    'base64_payload_valid':False,'native_pkey_exit':result.returncode,
    'native_pkey_stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
print(json.dumps({'scope':'Only the six listed own-package manual files',
 'source_archive_sha256':digest(source),'package_archive_sha256':digest(package),
 'package_record_sha256':digest(record_path),'native_openssl':native_version,
 'classifications':rows,'raw_marker_findings_suppressed':False,
 'whole_image_credential_audit_accepted':False,'installed_target_modified':False},indent=2))
'''


def main():
    result = subprocess.run(ssh_args() + ['python3 -B -'], input=REMOTE,
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    raw = result.stdout.encode()
    report = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h11-openssl-document-markers-' + sha + '.json')
    path.write_bytes(raw)
    print(json.dumps({'report': str(path), 'sha256': sha,
                      'classified_documents': len(report['classifications']),
                      'whole_image_credential_audit_accepted': False}))


if __name__ == '__main__':
    main()
