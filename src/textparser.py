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
    """
    Parses the given text and yields tokens which represent words within
    the given text. Tokens are assumed to be divided by any form of
    whitespace character. Results can be optionally be all returned in
    lowercase format by setting the remove_case parameter to True.
    """
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

    if s_buffer:
        yield s_buffer


def isnumeric(text):
    """
    Returns a True if the text is purely numeric and False otherwise.
    """
    try:
        float(text)
    except ValueError:
        return False
    else:
        return True
