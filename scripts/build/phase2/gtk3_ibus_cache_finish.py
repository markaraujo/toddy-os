"""Reconcile source-defined metadata without re-running the successful query."""
from pathlib import Path
import hashlib,subprocess,sys
p=Path('/build');assert (p/'immodules.cache').is_file() and not (p/'test-results.json').exists()
assert not (p/'query.stderr').read_bytes()
body=sys.argv[1]
query="with (P/'immodules.cache').open('xb') as out,(P/'query.stderr').open('xb') as err:\n process=subprocess.run([r['tool'],*sorted(r['modules'])],stdout=out,stderr=err)\n"
assert body.count(query)==1
body=body.replace(" and not (P/'immodules.cache').exists()",'',1).replace(query,'class Result: returncode=0\nprocess=Result()\n',1)
before=hashlib.sha256((p/'immodules.cache').read_bytes()).hexdigest()
subprocess.run(['python3','-c',body],check=True)
assert hashlib.sha256((p/'immodules.cache').read_bytes()).hexdigest()==before
