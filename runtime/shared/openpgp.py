"""Public OpenPGP packet custody; no crypto, keys, subprocess or installer import.

Same bounded binary parser used by the qualified offline-payload trust path.
Signature verification remains the caller's separate gpgv responsibility.
"""

def public_key_only(data):
    """Reject secret OpenPGP packets before copying a reviewed binary keyring."""
    if not isinstance(data, bytes) or not 0 < len(data) <= 1024 * 1024:
        raise ValueError('public_keyring_required')
    offset = 0
    public_key = False
    while offset < len(data):
        header = data[offset]
        offset += 1
        if not header & 0x80:
            raise ValueError('public_keyring_required')
        if header & 0x40:
            tag = header & 63
            if offset >= len(data):
                raise ValueError('public_keyring_required')
            first = data[offset]
            offset += 1
            if first < 192:
                length = first
            elif first < 224 and offset < len(data):
                length = ((first - 192) << 8) + data[offset] + 192
                offset += 1
            elif first == 255 and offset + 4 <= len(data):
                length = int.from_bytes(data[offset:offset + 4], 'big')
                offset += 4
            else:
                raise ValueError('unqualified_public_key_packet')
        else:
            tag = (header >> 2) & 15
            width = (1, 2, 4, 0)[header & 3]
            if width == 0 or offset + width > len(data):
                raise ValueError('unqualified_public_key_packet')
            length = int.from_bytes(data[offset:offset + width], 'big')
            offset += width
        if tag not in (2, 6, 12, 13, 14, 17):
            raise ValueError('nonpublic_key_packet')
        public_key |= tag == 6
        offset += length
        if offset > len(data):
            raise ValueError('truncated_public_key_packet')
    if not public_key:
        raise ValueError('public_keyring_required')
