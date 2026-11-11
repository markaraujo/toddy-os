"""Read only the pinned security source once; retain exact critical metadata."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT=Path(__file__).resolve().parents[2]
SELECTED={
    'browser/config/version.txt','browser/config/version_display.txt',
    'config/milestone.txt','build/moz.configure/rust.configure',
    'build/moz.configure/toolchain.configure','build/moz.configure/nss.configure',
    'build/moz.configure/nspr.configure','toolkit/moz.configure','moz.configure',
    'LICENSE','toolkit/content/license.html','media/libpng/moz.yaml',
    'media/libpng/LICENSE','media/libpng/png.h','media/libvpx/moz.yaml',
    'media/libwebp/moz.yaml','media/libaom/moz.yaml','media/libdav1d/moz.yaml',
    'parser/expat/moz.yaml','security/nss/lib/nss/nss.h',
    'nsprpub/pr/include/prinit.h',
}


def main():
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='firefox-security-1537')
    archive=ROOT/'.local/sources'/row['filename']
    assert archive.is_file() and not archive.is_symlink()
    with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
    directory=ROOT/'.local/phase2/firefox-security-source-review-1'
    assert not directory.exists(),'Inspect existing scan/result; never repeat completed source review'
    directory.mkdir(mode=0o700)
    state={'state':'scanning','source':row,'members':0,'expanded_bytes':0,'selected':{}}
    receipt=directory/'result.json'
    receipt.write_text(json.dumps(state,indent=2)+'\n')
    with tarfile.open(archive,mode='r|xz') as bundle:
        for member in bundle:
            parts=Path(member.name).parts
            if not parts:
                assert member.isdir();continue
            assert not member.name.startswith('/') and '..' not in parts
            assert parts[0]=='firefox-153.7.0'
            state['members']+=1
            if member.isfile():state['expanded_bytes']+=member.size
            relative='/'.join(parts[1:])
            if relative in SELECTED:
                assert member.isfile() and member.size<=2*1024**2
                data=bundle.extractfile(member).read()
                destination=directory/'selected'/relative
                destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
                state['selected'][relative]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    assert SELECTED<=set(state['selected']),sorted(SELECTED-set(state['selected']))
    assert (directory/'selected/browser/config/version.txt').read_text().strip()=='153.7.0'
    assert (directory/'selected/browser/config/version_display.txt').read_text().strip()=='153.7.0esr'
    state.update(state='complete',scope='Read-only source metadata/version/license inventory; no extraction into guest, compatibility/ABI/build/security acceptance')
    receipt.write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps({k:v for k,v in state.items() if k!='selected'}))


if __name__=='__main__':main()
