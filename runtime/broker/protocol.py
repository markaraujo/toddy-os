"""Bounded strict worker framing shared by the B01 spike and future broker."""
import json
import math
import os
import select
import struct
import time

MAX_FRAME = 1024 * 1024


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result

    def constant(_):
        raise ValueError('nonfinite_json')

    result = json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                        parse_constant=constant)

    def validate(value, depth=0):
        if depth > 64:
            raise ValueError('json_depth')
        if isinstance(value, str):
            value.encode('utf-8', errors='strict')
        elif isinstance(value, dict):
            for key, item in value.items():
                validate(key, depth + 1)
                validate(item, depth + 1)
        elif isinstance(value, list):
            for item in value:
                validate(item, depth + 1)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(value) or (value == int(value) and abs(value) > 2**53 - 1):
                raise ValueError('json_number_range')
    validate(result)
    return result


def encode(message):
    body = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    if not 0 < len(body) <= MAX_FRAME:
        raise ValueError('frame_length')
    strict_json(body)
    return struct.pack('>I', len(body)) + body


def read_frame(stream, timeout=5):
    deadline = time.monotonic() + timeout

    def exact(count):
        chunks = bytearray()
        while len(chunks) < count:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([stream.fileno()], [], [], remaining)[0]:
                raise TimeoutError('worker_frame_deadline')
            chunk = os.read(stream.fileno(), count - len(chunks))
            if not chunk:
                raise EOFError('truncated_frame')
            chunks.extend(chunk)
        return bytes(chunks)

    size = struct.unpack('>I', exact(4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('frame_length')
    return strict_json(exact(size))
