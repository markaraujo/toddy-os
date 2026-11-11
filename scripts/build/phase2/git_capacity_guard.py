"""Bound disposable Git compiler/test output; never accept a reserve stop."""
from pathlib import Path
import json,os,shutil,signal,subprocess,sys,time
assert os.getuid()==101
p=subprocess.Popen(sys.argv[1:],stdin=subprocess.DEVNULL,start_new_session=True)
minimum=shutil.disk_usage('/build').free;reason=None;started=time.monotonic()
while p.poll() is None:
 free=shutil.disk_usage('/build').free;minimum=min(minimum,free)
 if free<128*1024**2:
  reason='workspace-reserve';os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=15)
  break
 time.sleep(.25)
minimum=min(minimum,shutil.disk_usage('/build').free)
r={'command':sys.argv[1:],'exit':p.returncode,'stop_reason':reason,'minimum_free_bytes':minimum,'elapsed_seconds':round(time.monotonic()-started,3)}
Path('/build/capacity-result.json').write_text(json.dumps(r,indent=2)+'\n')
raise SystemExit(70 if reason else p.returncode)
