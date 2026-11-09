"""Accept only Meson's observed removal of GJS's private build RUNPATH."""
import hashlib
import struct


def sections(data):
    assert data[:7] == b'\x7fELF\x02\x01\x01' and len(data) >= 64
    offset = struct.unpack_from('<Q', data, 40)[0]
    size, count, names_index = struct.unpack_from('<HHH', data, 58)
    assert size == 64 and 0 < count < 4096 and names_index < count
    assert offset + size * count <= len(data)
    headers = [struct.unpack_from('<IIQQQQIIQQ', data, offset + i * size) for i in range(count)]
    names_header = headers[names_index]
    names = data[names_header[4]:names_header[4] + names_header[5]]
    result = {}
    for header in headers:
        assert header[0] < len(names)
        end = names.find(b'\0', header[0])
        assert end >= 0
        name = names[header[0]:end].decode('ascii')
        assert name not in result
        result[name] = (header[4], header[5])
    return result


def validate_transition(compiled, staged):
    assert len(compiled) == len(staged)
    original_sections = sections(compiled)
    assert original_sections == sections(staged)
    dynamic_offset, dynamic_size = original_sections['.dynamic']
    strings_offset, strings_size = original_sections['.dynstr']
    assert dynamic_size % 16 == 0 and dynamic_offset + dynamic_size <= len(compiled)
    assert strings_offset + strings_size <= len(compiled)
    def entries(data):
        values = []
        for offset in range(dynamic_offset, dynamic_offset + dynamic_size, 16):
            tag, value = struct.unpack_from('<qQ', data, offset)
            if tag == 0:
                break
            values.append((tag, value))
        return values
    old = entries(compiled)
    new = entries(staged)
    paths = [(tag, value) for tag, value in old if tag in (15, 29)]
    assert len(paths) == 1 and paths[0][0] == 29
    assert not any(tag in (15, 29) for tag, _ in new)
    assert [(tag, value) for tag, value in old if tag not in (15, 29)] == new
    start = strings_offset + paths[0][1]
    assert strings_offset <= start < strings_offset + strings_size
    end = compiled.find(b'\0', start, strings_offset + strings_size)
    assert end >= start and compiled[start:end] == b'$ORIGIN/'
    assert staged[start:end] == b'X' * (end - start)
    # Meson depfixer moves the removed entry (now DT_NULL, same value)
    # immediately after the original first DT_NULL; unused slots stay intact.
    expected = bytearray(compiled)
    expected[start:end] = b'X' * (end - start)
    transformed = new + [(0, 0), (0, paths[0][1])]
    assert old and struct.unpack_from('<qQ', compiled, dynamic_offset + len(old) * 16) == (0, 0)
    assert len(transformed) * 16 <= dynamic_size
    for index, entry in enumerate(transformed):
        struct.pack_into('<qQ', expected, dynamic_offset + index * 16, *entry)
    assert expected == staged, 'Bytes changed beyond exact Meson RUNPATH removal'
    return {'scope': 'Exact Meson install RUNPATH removal only; all other dynamic entries and ELF bytes identical',
            'compiled_sha256': hashlib.sha256(compiled).hexdigest(),
            'staged_sha256': hashlib.sha256(staged).hexdigest(),
            'removed_runpath': '$ORIGIN/',
            'different_bytes': sum(a != b for a, b in zip(compiled, staged))}
