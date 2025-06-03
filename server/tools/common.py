# coding: utf-8

"""
The common helping functions
"""

import re
from urllib.parse import urlparse
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

def to_doc_source(repo: str, branch: str, commit: str):
    url = urlparse(repo)
    url.hostname
    dot_git_index = url.path.index(".git")
    return f"{url.hostname}/{url.path[1:dot_git_index]}/tree/{branch}@{commit}"

if __name__ == '__main__':
    assert is_empty('')
    assert is_empty('""')
    assert is_empty('    ')
    assert is_empty('"')
    assert is_empty('" "')
    assert not is_empty('a')
    assert not is_empty('"a"')
    print(to_doc_source("https://github.com/stolostron/rhacm-docs.git", "2.13_prod", "abc123"))
