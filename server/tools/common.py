# coding: utf-8

"""
The common helping functions
"""

import re
import tiktoken

def is_empty(s: str) -> bool:
    if not s:
        return True

    striped = replace_start(s, '"', '')
    striped = replace_end(striped, '"', '')

    if len(striped.strip()) == 0:
        return True

    return False

def replace_start(s: str, old_value: str, new_value: str):
    return re.sub(f'^{old_value}', new_value, s)

def replace_end(s: str, old_value: str, new_value: str):
    return re.sub(f'{old_value}$', new_value, s)

def count_tokens(text, encoding_name='cl100k_base'):
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

if __name__ == '__main__':
    assert is_empty('')
    assert is_empty('""')
    assert is_empty('    ')
    assert is_empty('"')
    assert is_empty('" "')
    assert not is_empty('a')
    assert not is_empty('"a"')
