"""Extract only a validated UCD data ZIP into a fresh immutable-input tree."""
from pathlib import Path,PurePosixPath
import hashlib,re,stat,zipfile
def extract_ucd(archive,destination):
    destination=Path(destination)
    assert not destination.exists(),'Inspect existing UCD input before any replay'
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist();names=set();total=0
        for member in entries:
            path=PurePosixPath(member.filename);mode=member.external_attr>>16
            if path.is_absolute() or any(p in ['','.','..'] for p in member.filename.rstrip('/').split('/')) or not re.fullmatch(r'[A-Za-z0-9_.\-/]+',member.filename):raise ValueError('Unsafe UCD data path')
            if member.filename in names:raise ValueError('Duplicate UCD data path')
            names.add(member.filename)
            if stat.S_IFMT(mode) not in [0,stat.S_IFREG,stat.S_IFDIR]:raise ValueError('Special UCD data entry')
            if member.flag_bits&1:raise ValueError('Encrypted UCD data entry')
            total+=member.file_size
            if member.file_size>32*1024**2 or total>128*1024**2 or len(entries)>256:raise ValueError('Oversized UCD data')
        if z.testzip() is not None:raise ValueError('UCD ZIP CRC failure')
        assert {'ReadMe.txt','UnicodeData.txt','NamesList.txt','Blocks.txt'}<=names
        assert b'Version 17.0.0' in z.read('ReadMe.txt')
        destination.mkdir();data=destination/'ucd';data.mkdir();manifest={}
        for member in entries:
            p=data/member.filename
            if member.is_dir():p.mkdir(parents=True,exist_ok=True);continue
            p.parent.mkdir(parents=True,exist_ok=True);contents=z.read(member)
            p.write_bytes(contents);p.chmod(0o644);manifest[member.filename]=hashlib.sha256(contents).hexdigest()
    return manifest
