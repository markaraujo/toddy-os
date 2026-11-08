#!/usr/bin/env python3
"""Pin one selected BLFS leaf from its frozen page and official HTTPS archive."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
import phase2_dependency_graph as graph

ROOT=Path(__file__).resolve().parents[2]


def reference_scope(tree, anchor):
    if not anchor:return tree
    parents={child:parent for parent in tree.iter() for child in parent}
    found=next((e for e in tree.iter() if e.get('id')==anchor),None)
    assert found is not None,'Missing package anchor'
    while found in parents:
        found=parents[found]
        if found.tag.endswith('}div') and found.get('class')=='sect2':return found
    raise AssertionError('Package anchor has no scoped section')


def dependency_reference_allowed(reference, parent_name, components, read_node=graph.node):
    parents=[row for row in components if row['name']==parent_name]
    assert len(parents)==1, 'Select one already frozen parent source'
    parent=parents[0]
    assert parent['reference'].startswith('BLFS13.1-systemd ')
    parent_ref=parent['reference'].removeprefix('BLFS13.1-systemd ')
    assert re.fullmatch(r'[A-Za-z0-9/_+.-]+[.]html(?:#[A-Za-z0-9_+.-]+)?',parent_ref)
    node=read_node(parent_ref)
    assert node['book_page_sha256']==parent['book_page_sha256']
    return any(edge['reference']==reference and edge['kind'] in {'required','recommended'}
               for edge in node['edges'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference');parser.add_argument('name');parser.add_argument('version')
    parser.add_argument('--dependency-of', help='Explicit required/recommended dependency of one already frozen leaf')
    args=parser.parse_args()
    assert re.fullmatch(r'[a-z0-9][a-z0-9+.-]{0,95}',args.name)
    assert re.fullmatch(r'[0-9][a-zA-Z0-9._+-]{0,95}',args.version)
    nodes=json.loads((ROOT/'config/phase2/desktop-dependencies.json').read_text())['nodes']
    selected=args.reference in nodes or any(e['reference']==args.reference for n in nodes.values() for e in n['edges'])
    if not selected and args.dependency_of:
        components=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
        selected=dependency_reference_allowed(args.reference,args.dependency_of,components)
    assert selected, 'Source must belong to the selected graph or an explicit frozen-parent dependency'
    node=nodes.get(args.reference) or graph.node(args.reference)
    filename,_,anchor=args.reference.partition('#')
    page=graph.BOOK/filename;raw=page.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==node['book_page_sha256']
    tree=graph.ET.fromstring(re.sub(r'&([A-Za-z][A-Za-z0-9]*);',graph.entity,raw.decode()))
    tree=reference_scope(tree,anchor)
    url=md5=None
    for paragraph in tree.findall('.//x:p',graph.NS):
        text=' '.join(''.join(paragraph.itertext()).split())
        if text.startswith('Download (HTTP):') and url is None:
            url=paragraph.find('.//x:a',graph.NS).get('href')
        if text.startswith('Download MD5 sum:') and md5 is None:
            md5=text.rsplit(' ',1)[-1]
    parsed=urlsplit(url)
    assert parsed.scheme=='https' and not parsed.username and not parsed.password
    assert re.fullmatch(r'[a-f0-9]{32}',md5)
    filename=Path(parsed.path).name
    assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]{1,180}',filename)
    assert args.version in filename or args.version.replace('.','_') in filename
    target=ROOT/'.local/sources'/filename
    if not target.exists():
        part=target.with_name(filename+'.part');assert not part.exists(),'Inspect partial download first'
        subprocess.run(['curl','--fail','--silent','--show-error','--location','--connect-timeout','15',
                        '--max-time','180','--output',str(part),url],check=True)
        part.rename(target)
    assert target.is_file() and not target.is_symlink()
    data=target.read_bytes();assert hashlib.md5(data,usedforsecurity=False).hexdigest()==md5
    row={'name':args.name,'version':args.version,'filename':filename,'url':url,
         'sha256':hashlib.sha256(data).hexdigest(),'reference':'BLFS13.1-systemd '+args.reference,
         'book_page_sha256':node['book_page_sha256'],'book_md5':md5,
         'integrity':'Official HTTPS source matched frozen book legacy MD5; SHA256 frozen before guest extraction/use',
         'status':'source_verified'}
    path=ROOT/'config/phase2/sources.lock.json';lock=json.loads(path.read_text())
    prior=[r for r in lock['components'] if r['name']==args.name]
    if prior:assert len(prior)==1 and prior[0]==row,'Do not replace a frozen source silently'
    else:lock['components'].append(row);path.write_text(json.dumps(lock,indent=2)+'\n')
    print(json.dumps(row,indent=2))
