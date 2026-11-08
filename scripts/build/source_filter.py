"""Narrow upstream test-fixture exceptions to safe tar extraction."""
import copy
import os
import tarfile

DPKG_FIFOS = frozenset({
    'dpkg-1.22.22/tests/t-unpack-fifo/pkg-fifo/test-fifo',
    'dpkg-1.22.22/tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link0',
    'dpkg-1.22.22/tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link1',
})


def source_filter(filename):
    def filtered(member, destination):
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
