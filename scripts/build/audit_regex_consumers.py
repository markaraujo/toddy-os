#!/usr/bin/env python3
"""Measure native text-consumer case folding; keep known limitations explicit."""
import json
import subprocess


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    results=[]
    examples=[('en_US.UTF-8','task'.encode(),'TASK'.encode(),'required-english'),
              ('pt_BR.UTF-8','ação'.encode(),'AÇÃO'.encode(),'required-portuguese'),
              ('en_US.UTF-8','ς'.encode(),'Σ'.encode(),'greek-utf8'),
              ('el_GR.iso88597',b'\xf2',b'\xd3','greek-single-byte')]
    for locale,text,pattern,scope in examples:
        for program in ['grep','sed','gawk','bash']:
            environment=['LC_ALL='+locale]
            base=['chroot','/mnt/lfs','/usr/bin/env',*environment]
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
        command=['chroot','/mnt/lfs','/usr/bin/env','LC_ALL='+locale,'GAWK_GNU_MATCHERS=1',
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
            'known_failures':failed,'results':results,'scope':'Target chroot text-consumer probes; not full regex or native boot acceptance'}
    print(json.dumps(report,indent=2))
    if not required_pass or failed!=expected:raise SystemExit('Unexpected regex outcome; investigate before accepting audit')

if __name__=='__main__':main()
