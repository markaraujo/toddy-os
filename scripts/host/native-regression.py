#!/usr/bin/env python3
"""H12 native execution of preserved Glibc tests and Systemd namespaces."""
import base64
import hashlib
import json
import os
import pwd
from pathlib import Path
import re
import runpy
import shlex
import signal
import subprocess
import tempfile
import termios
import time
import zlib


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(report):
    data=json.dumps(report,sort_keys=True).encode()
    encoded=base64.b64encode(zlib.compress(data,9)).decode()
    chunks=[encoded[i:i+2048] for i in range(0,len(encoded),2048)]
    summary={'complete':report['complete'],'tests':len(report['results']),
             'passed':sum(row['passed'] for row in report['results']),
             'chunks':len(chunks),'report_sha256':hashlib.sha256(data).hexdigest(),
             'workspace':report['workspace']}
    # A dedicated second UART avoids journal/console rate limits and getty output.
    fd=os.open('/dev/ttyS1',os.O_RDWR|os.O_NOCTTY)
    attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0
    attrs[2]=termios.CS8|termios.CREAD|termios.CLOCAL
    attrs[4]=attrs[5]=termios.B115200
    termios.tcsetattr(fd,termios.TCSANOW,attrs)
    with os.fdopen(fd,'w',buffering=1) as stream:
        for index,chunk in enumerate(chunks):
            stream.write(f'TODDY_NATIVE_REGRESSIONS_DATA {index} {chunk}\n')
        stream.write('TODDY_NATIVE_REGRESSIONS_RESULT '+json.dumps(summary)+'\n')
        stream.flush();termios.tcdrain(stream.fileno())
    print('TODDY_NATIVE_REGRESSIONS_RESULT '+json.dumps(summary),flush=True)
    return data


def main():
    runpy.run_path(str(Path(os.environ['CREDENTIALS_DIRECTORY'])/'toddy.boot-common'))['main']()
    build=Path('/sources/glibc-2.44/build');original=(build/'tests.sum').read_bytes();selected=[]
    for line in original.decode().splitlines():
        if not line.startswith('UNSUPPORTED: '):continue
        name=line.split(': ',1)[1]
        if not re.fullmatch(r'[a-z0-9_-]+/[A-Za-z0-9_.-]+',name):raise ValueError('Unexpected test name')
        p=build/(name+'.out');text=p.read_text(errors='replace') if p.exists() else ''
        if any(reason in text for reason in ('CLONE_NEWUSER','apparmor_restrict_unprivileged_userns','unshare','ptrace')):selected.append(name)
    if len(selected)!=48 or len(set(selected))!=48:raise ValueError('Native retest selection changed')
    selected.append('io/tst-lchmod')
    for built,installed in [('libc.so','/usr/lib/libc.so.6'),('elf/ld.so','/usr/lib/ld-linux-x86-64.so.2')]:
        if digest(build/built)!=digest(Path(installed)):raise ValueError('Preserved Glibc runtime differs from installed bytes')
    work=Path(tempfile.mkdtemp(prefix='toddy-native-regressions-',dir='/var/tmp'))
    binaries=[build/name for name in selected]+[build/'support/test-container',build/'libc.so',build/'elf/ld.so']
    before={str(p):digest(p) for p in binaries}
    report={'complete':False,'workspace':str(work),'kernel':os.uname().release,
            'original_glibc_summary_sha256':hashlib.sha256(original).hexdigest(),
            'selected_glibc_tests':selected,'results':[],'global_security_controls_changed':False,
            'source_sha256':{name:digest(build.parent/name) for name in ('Makefile','Makeconfig','Rules','scripts/evaluate-test.sh')},
            'preserved_binary_sha256':before,
            'core_binary_sha256':{name:digest(Path(name)) for name in ('/usr/lib/libc.so.6','/usr/lib/systemd/systemd')},
            'raw_evidence':{}}
    raw=report['raw_evidence'];print('TODDY_NATIVE_REGRESSIONS_WORKSPACE '+str(work),flush=True)
    def save():
        p=work/'progress.json.part';p.write_text(json.dumps(report,indent=2)+'\n');p.replace(work/'progress.json')
    def run(name,argv,cwd,timeout,identity=None):
        start=time.monotonic();logpath=work/(name.replace('/','_')+'.log')
        def demote():
            os.setgroups([]);os.setgid(identity.pw_gid);os.setuid(identity.pw_uid)
        with logpath.open('xb') as log:
            process=subprocess.Popen(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,
                env={'PATH':'/usr/bin:/usr/sbin','HOME':identity.pw_dir if identity else '/root','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},
                start_new_session=True,preexec_fn=demote if identity else None)
            timed_out=False
            try:process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(process.pid,signal.SIGKILL);process.wait()
        data=logpath.read_bytes();raw.setdefault(name,{})['command_log']=base64.b64encode(data).decode()
        row={'test':name,'argv':argv,'cwd':str(cwd),'uid':identity.pw_uid if identity else 0,'exit':process.returncode,'timeout':timed_out,
             'seconds':time.monotonic()-start,'log_sha256':hashlib.sha256(data).hexdigest(),'passed':False}
        report['results'].append(row);save();print('TODDY_NATIVE_REGRESSION_STEP '+json.dumps(row),flush=True)
        return row
    save()
    systemd=run('systemd-test-namespace',['/sources/systemd-261.2/build/test-namespace'],'/',120)
    systemd['passed']=systemd['exit']==0 and not systemd['timeout']
    for name in selected:
        raw[name]={'original':{}}
        for suffix in ('.out','.test-result'):
            p=build/(name+suffix)
            if p.is_file():raw[name]['original'][suffix]=base64.b64encode(p.read_bytes()).decode()
        # Expand the frozen upstream rule without compiling or executing it.
        # Its expected stdout redirection identifies exactly this test's command.
        planning=subprocess.run(['make','-n','-W',str(build/name),'test','t='+name],cwd=build,
            env={'PATH':'/usr/bin:/usr/sbin','HOME':'/root','LC_ALL':'C'},capture_output=True,text=True,timeout=30)
        (work/(name.replace('/','_')+'.make-dry-run')).write_text(planning.stdout+planning.stderr)
        planning.check_returncode()
        text=planning.stdout.replace('\\\n',' ');suffix=' > '+str(build/name)+'.out; '
        matches=[line.split(suffix)[0] for line in text.splitlines() if suffix in line]
        if len(matches)!=1:raise ValueError('Missing/ambiguous frozen test command: '+name)
        argv=shlex.split(matches[0])
        if (argv[0]!='env' or argv.count(str(build/name))!=1
                or any(any(c in token for c in (';','`','|','&','\n','$')) for token in argv)):
            raise ValueError('Unexpected frozen command structure: '+name)
        if name=='stdlib/tst-system':
            # Its RLIMIT_NPROC branch must execute as a non-root UID. The
            # upstream pristine sysroot has no passwd and maps only the caller.
            # Give only a fresh disposable mutable fixture and its lock to tester.
            identity=pwd.getpwnam('tester')
            if identity.pw_uid==0:raise ValueError('Require an unprivileged test identity')
            mutable=build/'testroot.root';lockfile=build/'testroot.pristine/lock.fd'
            if mutable.resolve()!=mutable or not mutable.is_dir() or lockfile.resolve()!=lockfile or not lockfile.is_file():
                raise ValueError('Unexpected generated container fixture')
            previous=lockfile.stat();lock_sha=digest(lockfile)
            preserved=work/'container-root-before-unprivileged-system'
            mutable.rename(preserved)
            mutable.mkdir(mode=0o755);os.chown(mutable,identity.pw_uid,identity.pw_gid)
            os.chown(lockfile,identity.pw_uid,identity.pw_gid)
            try:row=run(name,argv,build.parent/Path(name).parent,120,identity)
            finally:
                os.chown(lockfile,previous.st_uid,previous.st_gid)
                # Later root-mapped tests must not inherit tester-owned device
                # nodes. Retain the private result, then restore the exact root.
                mutable.rename(work/'container-root-unprivileged-system-result')
                preserved.rename(mutable)
            if digest(lockfile)!=lock_sha:raise ValueError('Container lock contents changed')
            row['fixture_policy']='Fresh mutable container root only; original root and lock owner restored; private result retained; no account/syscall/test changes'
        else:
            row=run(name,argv,build.parent/Path(name).parent,120)
        row['dry_run_sha256']=hashlib.sha256(planning.stdout.encode()).hexdigest()
        evaluated=subprocess.check_output(['/bin/sh',str(build.parent/'scripts/evaluate-test.sh'),name,str(row['exit']),'false','false'],text=True)
        raw[name]['.test-result']=base64.b64encode(evaluated.encode()).decode()
        row['test_result']=evaluated.strip()
        row['passed']=not row['timeout'] and row['exit']==0 and evaluated.splitlines()==['PASS: '+name,'original exit status 0']
        save()
    after={str(p):digest(p) for p in binaries}
    report['preserved_binaries_unchanged']=before==after
    report['complete']=before==after and all(row['passed'] for row in report['results'])
    (work/'result.json').write_bytes(json.dumps(report,sort_keys=True).encode())
    export(report)
    if not report['complete']:raise RuntimeError('Native regression failures retained')


if __name__=='__main__':
    try:main()
    except BaseException as error:
        print('TODDY_NATIVE_REGRESSIONS_FAIL '+str(error),flush=True);raise
