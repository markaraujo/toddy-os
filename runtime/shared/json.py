"""Strict bounded JSON contract shared by lightweight UI and optional agent."""
import json
import math


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

