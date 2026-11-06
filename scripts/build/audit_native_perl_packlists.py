#!/usr/bin/env python3
"""Read installed packlists with native Perl and verify canonical ownership."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
from audit_native_elf import target_resolve


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    root=Path('/mnt/lfs');owners=defaultdict(set);findings=[]
    output=subprocess.check_output(['dpkg-query','--admindir='+str(root/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'],text=True)
    for line in output.splitlines():
        name,version,arch,status=line.split('\t')
        if status!='install ok installed':continue
        record=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
        for path,entry in record['payload'].items():
            if not entry.get('directory'):owners[path].add(name)
    files=['/'+str(p.relative_to(root)) for p in sorted((root/'usr/lib/perl5').rglob('.packlist'))]
    program='''use ExtUtils::Packlist; use JSON::PP;
my @rows; for my $file (@ARGV) {
 my $list=ExtUtils::Packlist->new($file);
 push @rows,{file=>$file,entries=>[sort keys %$list]};
} print JSON::PP->new->canonical->encode(\\@rows);'''
    rows=json.loads(subprocess.check_output(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','/usr/bin/perl','-e',program,*files],text=True))
    for row in rows:
        providers=owners[row['file']]
        if len(providers)!=1:
            findings.append({'file':row['file'],'problem':'Packlist lacks unique native owner'});continue
        package=next(iter(providers))
        for entry in row['entries']:
            if not entry.startswith('/usr/') or '..' in Path(entry).parts:
                findings.append({'file':row['file'],'entry':entry,'problem':'Noncanonical installed path'});continue
            actual,canonical=target_resolve(root,entry)
            if not actual.is_file() or owners.get(canonical)!=providers:
                findings.append({'file':row['file'],'entry':entry,'package':package,'problem':'Missing or differently owned module payload'})
    print(json.dumps({'scope':'Native ExtUtils::Packlist parsing and installed file ownership only','packlists':len(rows),'entries':sum(len(r['entries']) for r in rows),'findings':findings},indent=2))

if __name__=='__main__':main()
