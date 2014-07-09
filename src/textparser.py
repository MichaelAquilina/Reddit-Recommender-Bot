import nltk
import unicodedata

from string import ascii_letters, whitespace, digits, punctuation
from HTMLParser import HTMLParser


# Stemmer interface which returns token unchanged
class NullStemmer(object):

    def stem(self, x):
        return x

    def __str__(self):
        return '<NullStemmer>'

_parser = HTMLParser()
_stopwords = frozenset(nltk.corpus.stopwords.words())
_accepted = frozenset(ascii_letters + digits + punctuation) - set('\'')


def normalize_unicode(text):
    """
    Normalize any unicode characters to ascii equivalent
    https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
    """
    if type(text) == unicode:
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
    else:
        return text


def word_tokenize(text, stopwords=_stopwords, html=False):
    """
    Parses the given text and yields tokens which represent words within
    the given text. Tokens are assumed to be divided by any form of
    whitespace character.
    """
    s_buffer = u''
    for c in text:
        if c in whitespace:
            token = s_buffer
            if html:
                token = _parser.unescape(token)

            token = token.strip(punctuation)
            if len(token) > 1 and token not in stopwords and not isnumeric(token):
                yield token
            s_buffer = u''
        elif c in _accepted:
            s_buffer += c.lower()

    token = s_buffer
    if html:
        token = _parser.unescape(token)
    token = token.strip(punctuation)
    if len(token) > 1 and token not in stopwords and not isnumeric(token):
        yield token


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
