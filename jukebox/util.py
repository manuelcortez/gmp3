"""Utility functions."""

import six

def convert(data):
    """Used to convert kwargs to use string-based keys and values, not bytes."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[convert(key)] = convert(value)
    elif isinstance(data, list):
        result = []
        for x in data:
            result.append(convert(x))
    elif isinstance(data, six.string_types) or isinstance(data, bytes):
        try:
            result = data.decode()
        except AttributeError as e:
            result = data
    else:
        result = data
    return result
