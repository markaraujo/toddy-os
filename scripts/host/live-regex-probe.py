#!/usr/bin/env python3
"""Measure native text-consumer case folding; keep known limitations explicit."""
import json
import subprocess
import os,sys,pathlib


def main():
    token,network=sys.argv[1:]
    assert os.getuid()==0 and os.uname().release=='7.1.8-toddy'
    assert pathlib.Path('/proc/1/comm').read_text().strip()=='systemd'
    assert subprocess.check_output(['tty'],text=True).strip()=='/dev/ttyS0'
    assert pathlib.Path('/run/toddy/live-session').is_file()
    results=[]
    examples=[('en_US.UTF-8','task'.encode(),'TASK'.encode(),'required-english'),
              ('pt_BR.UTF-8','ação'.encode(),'AÇÃO'.encode(),'required-portuguese'),
              ('en_US.UTF-8','ς'.encode(),'Σ'.encode(),'greek-utf8'),
              ('el_GR.iso88597',b'\xf2',b'\xd3','greek-single-byte')]
    for locale,text,pattern,scope in examples:
        for program in ['grep','sed','gawk','bash']:
            environment=['LC_ALL='+locale]
            base=['/usr/bin/env',*environment]
            if program=='grep':command=['grep','-i',pattern]
            elif program=='sed':command=['sed','-n',b'/'+pattern+b'/Ip']
            elif program=='gawk':command=['gawk','-v',b'p='+pattern,'BEGIN{IGNORECASE=1} $0~p {print}']
            else:command=['bash','-c','shopt -s nocasematch; [[ "$1" =~ "$2" ]] && printf "%s\n" "$1"','--',text,pattern]
            result=subprocess.run(base+command,input=text+b'\n',capture_output=True)
            results.append({'program':program,'locale':locale,'scope':scope,'exit':result.returncode,
                            'stdout_hex':result.stdout.hex(),'expected_stdout_hex':(text+b'\n').hex(),
                            'stderr':result.stderr.decode(errors='replace'),
                            'passed':result.returncode==0 and result.stdout==text+b'\n'})
    for locale,text,pattern,scope in examples[2:]:
        command=['/usr/bin/env','LC_ALL='+locale,'GAWK_GNU_MATCHERS=1',
                 'gawk','-v',b'p='+pattern,'BEGIN{IGNORECASE=1} $0~p {print}']
        result=subprocess.run(command,input=text+b'\n',capture_output=True)
        results.append({'program':'gawk-existing-gnu-matchers','locale':locale,'scope':scope,
                        'exit':result.returncode,'stdout_hex':result.stdout.hex(),
                        'expected_stdout_hex':(text+b'\n').hex(),'stderr':result.stderr.decode(errors='replace'),
                        'passed':result.returncode==0 and result.stdout==text+b'\n'})
    required_pass=all(r['passed'] for r in results if r['scope'].startswith('required-'))
    failed=[{'program':r['program'],'scope':r['scope']} for r in results if not r['passed']]
    expected=[{'program':'gawk','scope':'greek-utf8'},
              {'program':'gawk','scope':'greek-single-byte'},
              {'program':'bash','scope':'greek-single-byte'}]
    report={'decision':'ADR-0037','all_cases_pass':not failed,'required_pt_en_cases_pass':required_pass,
            'known_failures':failed,'results':results,'scope':'Final live console text-consumer probes; known Greek limitations preserved'}
    if not required_pass or failed!=expected:raise SystemExit('Unexpected regex outcome; investigate before accepting audit')
    report.update(token=token,firmware='uefi' if pathlib.Path('/sys/firmware/efi').is_dir() else 'bios',real_console_login=True)
    print('TODDY_LIVE_TEST_OK '+json.dumps(report,sort_keys=True),flush=True)
    subprocess.run(['systemctl','poweroff'],check=True)

if __name__=='__main__':
 try:main()
 except BaseException as error:print('TODDY_LIVE_TEST_FAIL '+str(error),flush=True);raise
