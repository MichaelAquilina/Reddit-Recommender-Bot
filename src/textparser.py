import unicodedata

from string import ascii_letters, whitespace, digits, punctuation

_accepted = frozenset(ascii_letters + digits + punctuation)


def normalize_unicode(text):
    """
    Normalize any unicode characters to ascii equivalent
    https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
    """
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')


def word_tokenize(text, remove_case=False):

    s_buffer = u''

    for c in text:
        if c in whitespace:
            if s_buffer:
                yield s_buffer
            s_buffer = u''
        elif c in _accepted:
            if remove_case:
                s_buffer += c.lower()
            else:
                s_buffer += c

        # Ignore punctuation and digits?

    if s_buffer:
        yield s_buffer
