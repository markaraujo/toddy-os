"""Exercise the real native CSS compiler, including include resolution/refusal."""
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    checks=[]
    def run(name,args,text=None,refusal=False):
        r=subprocess.run(args,input=text,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        assert (r.returncode!=0) if refusal else (r.returncode==0),(name,r.returncode,r.stderr)
        checks.append({'name':name,'native_exit':r.returncode,'expected_refusal':refusal,'stdout':r.stdout,'stderr':r.stderr})
        return r
    version=run('version',['sassc','--version']).stdout
    assert '3.6.2' in version and '3.6.6' in version
    css=run('nested-unicode',['sassc','-s','-t','expanded'],'$navy: #002040; .toddy { color: $navy; content: "ação 日本語"; &:hover { opacity: 0.9; } }').stdout
    assert '#002040' in css and '.toddy:hover' in css and 'ação 日本語' in css
    with tempfile.TemporaryDirectory(prefix='toddy-sassc-') as name:
        root=Path(name);(root/'_navy.scss').write_text('$navy: #002040;\n')
        css=run('private-include',['sassc','-s','-t','expanded','-I',str(root)],'@import "navy"; .toddy { color: $navy; }').stdout
        assert '#002040' in css
    bad=run('malformed-refusal',['sassc','-s'],'.toddy { color:;',refusal=True)
    assert bad.stderr.strip()
    print(json.dumps({'scope':'Native stylesheet build CLI, no GUI/catalog acceptance','checks':checks,'navy_nested_unicode':True,'private_include':True,'malformed_refusal':True}))


if __name__=='__main__':main()
