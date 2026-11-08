"""Actual process APIs required by lit's per-test timeout/child cleanup."""
import json
import os
import select
import subprocess
import sys
import psutil

assert psutil.__version__=='7.2.2'
me=psutil.Process();assert me.pid==os.getpid() and me.uids().effective==os.geteuid()
assert me.memory_info().rss>0 and me.cpu_times().user>=0
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
try:
    process=psutil.Process(child.pid)
    assert process.ppid()==os.getpid() and child.pid in {p.pid for p in me.children(recursive=True)}
    try:process.wait(timeout=.03)
    except psutil.TimeoutExpired:pass
    else:raise AssertionError('Live child did not time out')
    process.terminate();assert child.wait(timeout=2)==-15
finally:
    if child.poll() is None:child.kill();child.wait(timeout=2)
program='import subprocess,sys;child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);print(child.pid,flush=True);child.wait()'
parent=subprocess.Popen([sys.executable,'-c',program],stdout=subprocess.PIPE,text=True)
descendants=[]
try:
    assert select.select([parent.stdout],[],[],2)[0],'Child-tree fixture did not become ready'
    pid=int(parent.stdout.readline())
    descendants=psutil.Process(parent.pid).children(recursive=True)
    assert len(descendants)==1 and descendants[0].pid==pid and descendants[0].ppid()==parent.pid
    descendants[0].kill()
    assert parent.wait(timeout=2)==0,'Parent did not reap its killed child'
    assert not psutil.pid_exists(pid)
finally:
    for process in descendants:
        try:process.kill()
        except psutil.NoSuchProcess:pass
    if parent.poll() is None:parent.kill();parent.wait(timeout=2)
    parent.stdout.close()
print(json.dumps({'version':psutil.__version__,'uid':os.geteuid(),'own_process_memory_cpu':True,
                  'timeout_then_terminate_exit':-15,'recursive_child_kill_and_reap':True,
                  'scope':'Native lit consumer APIs only; no broad host/process/network upstream matrix'}))
