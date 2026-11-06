"""Normalize the simple path-only packlists produced by our frozen modules."""
from pathlib import Path, PurePosixPath


def plan_packlist_rewrites(root, package, paths=None, allowed=None):
    root=Path(root).resolve()
    paths=list(paths) if paths is not None else [
        '/'+str(p.relative_to(root)) for p in root.rglob('.packlist')]
    prefix='/sources/stage/'+package
    rewrites={}
    for virtual in paths:
        path=root/virtual.lstrip('/')
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Packlist escapes package root: '+virtual)
        original=path.read_text()
        entries=[]
        for line in original.splitlines():
            # Frozen MakeMaker outputs contain path-only records. Refuse a new
            # format rather than silently discarding attributes/escaping.
            if not line or any(c.isspace() for c in line):
                raise ValueError('Unexpected packlist record format')
            canonical=line[len(prefix):] if line.startswith(prefix+'/') else line
            if not canonical.startswith('/usr/') or '..' in PurePosixPath(canonical).parts:
                raise ValueError('Unexpected packlist destination: '+line)
            if allowed is not None and canonical not in allowed:
                raise ValueError('Packlist entry is not owned by this package: '+canonical)
            payload=root/canonical.lstrip('/')
            if payload.is_symlink() or not payload.resolve().is_relative_to(root) or not payload.is_file():
                raise ValueError('Missing or redirected packlist payload: '+canonical)
            entries.append(canonical)
        if len(entries)!=len(set(entries)):
            raise ValueError('Duplicate canonical packlist entry')
        normalized='\n'.join(entries)+'\n'
        if normalized!=original:rewrites[path]=normalized
    return rewrites


def normalize_packlists(root, package, paths=None, allowed=None):
    rewrites=plan_packlist_rewrites(root,package,paths,allowed)
    for path,text in rewrites.items():path.write_text(text)
    return ['/'+str(p.relative_to(Path(root))) for p in rewrites]


if __name__=='__main__':
    import argparse,json,re,subprocess
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('package')
    args=parser.parse_args()
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    if not re.fullmatch(r'perl-[a-z0-9+.-]+',args.package) or args.root.is_symlink() or args.root.resolve()!=Path('/mnt/lfs/sources/stage')/args.package:
        raise SystemExit('Packlist CLI requires the guarded module staging root')
    print(json.dumps({'normalized_packlists':normalize_packlists(args.root,args.package)}))
