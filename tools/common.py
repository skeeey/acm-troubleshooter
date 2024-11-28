# coding: utf-8

import tiktoken

def is_empty(s: str) -> bool:
    return (not s or len(s.strip()) == 0)

def count_tokens(text, encoding_name="cl100k_base"):
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))