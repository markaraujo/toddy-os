"""Structured source-built package backend; no repository/URL/flag from the model."""
from pathlib import Path
import re
from operations import run_command
from store import PolicyError


def validate_package(args):
    if not isinstance(args,dict) or set(args)!= {'action','packages'} or args['action'] not in ('install','upgrade','remove') or \
       not isinstance(args['packages'],list) or not 1<=len(args['packages'])<=16 or any(not isinstance(p,str) for p in args['packages']) or len(set(args['packages']))!=len(args['packages']):
        raise PolicyError('invalid_package_operation')
    for package in args['packages']:
        if not isinstance(package,str) or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]{0,95}(?:=[0-9][a-zA-Z0-9.+:~_-]{0,95})?',package) or \
           (args['action']=='remove' and '=' in package):
            raise PolicyError('invalid_package_operation')


def query(packages):
    # Raw stdout stays inside trusted code; only parsed status/version is returned.
    result=run_command({'argv':['/usr/bin/dpkg-query','--show','--showformat=${binary:Package}\t${db:Status-Status}\t${Version}\n',*packages],
                        'timeout_seconds':10},capture=True)
    records={};missing=set()
    for line in result.pop('_private_output').decode('utf-8',errors='strict').splitlines():
        prefix='dpkg-query: no packages found matching '
        if line.startswith(prefix) and line[len(prefix):] in packages:
            missing.add(line[len(prefix):]);continue
        parts=line.split('\t')
        if len(parts)!=3 or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?',parts[0]) or \
           not re.fullmatch(r'[a-z-]+',parts[1]) or not re.fullmatch(r'[0-9][a-zA-Z0-9.+:~_-]*',parts[2]):
            raise PolicyError('package_status_unverified')
        records[parts[0].split(':',1)[0]]= {'status':parts[1],'version':parts[2]}
    if result['exit'] and not (result['exit']==1 and missing):raise PolicyError('package_status_unverified')
    return records


def package_transaction(args,canceled):
    validate_package(args)
    if not all(Path(path).is_file() for path in ('/usr/bin/apt-get','/usr/bin/dpkg-query','/var/lib/dpkg/status')):
        raise PolicyError('native_package_backend_unavailable')
    packages=args['packages'];names=[package.split('=',1)[0] for package in packages]
    before=query(names)
    if args['action']=='upgrade' and any(before.get(name,{}).get('status')!='installed' for name in names):
        raise PolicyError('package_not_installed')
    audit=run_command({'argv':['/usr/bin/dpkg','--audit'],'timeout_seconds':10},capture=True)
    if audit['exit'] or audit['_private_output'].strip():raise PolicyError('package_recovery_required')
    if canceled():raise PolicyError('operation_canceled_before_package_write')
    action='remove' if args['action']=='remove' else 'install'
    command=['/usr/bin/apt-get','--assume-yes','--no-download','--no-install-recommends',
        '-o','APT::Get::AllowUnauthenticated=false','-o','Acquire::AllowInsecureRepositories=false',
        '-o','Dpkg::Use-Pty=0','-o','Dpkg::Options::=--force-confold','-o','Dpkg::Options::=--force-confdef']
    if action=='install':command+=['--no-remove']
    if args['action']=='upgrade':command+=['--only-upgrade']
    command+=[action,*packages]
    # No download during native mutation. Cancellation remains visible/durable,
    # but never kills dpkg/maintainer scripts in a write to meet a UI timer.
    # This is intentionally no fixed execution timeout: healthy transactions are
    # monitored; a stalled write is reconciled/recovered, never blindly replayed.
    result=run_command({'argv':command,'timeout_seconds':None},capture=True,drain_unbounded=True)
    raw=result.pop('_private_output')
    if result['exit'] or b'No sandbox user' in raw or b'Download is performed unsandboxed as root' in raw:
        raise PolicyError('package_transaction_requires_reconciliation')
    after=query(names)
    audit=run_command({'argv':['/usr/bin/dpkg','--audit'],'timeout_seconds':10},capture=True)
    if audit['exit'] or audit['_private_output'].strip():raise PolicyError('package_recovery_required')
    for package,name in zip(packages,names):
        record=after.get(name,{})
        if action=='remove':
            if record.get('status') in ('installed','unpacked','half-configured','half-installed'):
                raise PolicyError('package_postcondition_failed')
        elif record.get('status')!='installed' or ('=' in package and record.get('version')!=package.split('=',1)[1]):
            raise PolicyError('package_postcondition_failed')
    return {'verified':True,'backend':'native-apt-dpkg','action':args['action'],'packages':after,
            'configuration_policy':'preserve-owner-modified-conffiles','cancellation_requested':bool(canceled()),
            'cancellation_boundary':'completed native transaction; committed effects retained'}
