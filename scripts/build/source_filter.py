"""Narrow upstream test-fixture exceptions to safe tar extraction."""
import copy
import os
from pathlib import PurePosixPath
import tarfile

AUTOAR_ARCHIVE = 'gnome-autoar-0.4.5.tar.xz'
AUTOAR_REFERENCE = 'gnome-autoar-0.4.5/tests/files/extract/test-symlink-parent/reference/arextract'


def validate_source_members(filename, members):
    if filename != AUTOAR_ARCHIVE:
        return
    reference = PurePosixPath(AUTOAR_REFERENCE).parts
    matches = [m for m in members if PurePosixPath(m.name).parts == reference]
    if (len(matches) != 1 or matches[0].name != AUTOAR_REFERENCE
            or not matches[0].issym() or matches[0].linkname != '/tmp'
            or matches[0].size != 0):
        raise tarfile.FilterError('Frozen autoar negative fixture identity changed')
    for member in members:
        parts = PurePosixPath(member.name).parts
        if member.name.startswith('/') or '..' in parts:
            raise tarfile.FilterError('Frozen autoar source member path must stay relative')
        if len(parts) > len(reference) and parts[:len(reference)] == reference:
            raise tarfile.FilterError('Archive member traverses the negative fixture link')

DPKG_FIFOS = frozenset({
    'dpkg-1.22.22/tests/t-unpack-fifo/pkg-fifo/test-fifo',
    'dpkg-1.22.22/tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link0',
    'dpkg-1.22.22/tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link1',
})


def source_filter(filename):
    def filtered(member, destination):
        if (filename == AUTOAR_ARCHIVE and member.name == AUTOAR_REFERENCE
                and member.issym() and member.linkname == '/tmp'
                and member.size == 0):
            # Only a reference assertion in the authenticated upstream test
            # archive, never production data. The whole-archive preflight above
            # rejects duplicates/descendants before creating the source tree.
            regular = copy.copy(member)
            regular.type = tarfile.REGTYPE
            regular.linkname = ''
            safe = tarfile.data_filter(regular, destination)
            safe.type = tarfile.SYMTYPE
            safe.linkname = '/tmp'
            return safe
        if (filename == 'AppStream-1.1.6.tar.xz'
                and member.name == './AppStream-1.1.6/tests/samples/compose/usr/share/metainfo/org.example.nonexistent-badlink.metainfo.xml'
                and member.issym() and member.linkname == '/nonexistent'
                and member.size == 0):
            # Frozen upstream negative fixture, never a production link. Keep
            # path/permission checks and reject a referent on this machine.
            if os.path.lexists('/nonexistent'):
                raise tarfile.FilterError('Reviewed negative fixture target must remain absent')
            regular = copy.copy(member)
            regular.type = tarfile.REGTYPE
            regular.linkname = ''
            safe = tarfile.data_filter(regular, destination)
            safe.type = tarfile.SYMTYPE
            safe.linkname = '/nonexistent'
            return safe
        if (filename == 'dpkg_1.22.22.tar.xz' and member.name in DPKG_FIFOS
                and member.isfifo()):
            # Apply the standard path, permission and ownership checks first.
            regular = copy.copy(member)
            regular.type = tarfile.REGTYPE
            safe = tarfile.data_filter(regular, destination)
            safe.type = tarfile.FIFOTYPE
            return safe
        return tarfile.data_filter(member, destination)
    return filtered
