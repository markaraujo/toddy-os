"""Narrow upstream test-fixture exceptions to safe tar extraction."""
import copy
import tarfile

DPKG_FIFOS = frozenset({
    'dpkg-1.22.22/tests/t-unpack-fifo/pkg-fifo/test-fifo',
    'dpkg-1.22.22/tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link0',
    'dpkg-1.22.22/tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link1',
})


def source_filter(filename):
    def filtered(member, destination):
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
