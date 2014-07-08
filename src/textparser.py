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
_accepted = frozenset(ascii_letters + digits + punctuation)


def clean_token(token):
    """
    Performs several cleaning steps on the given token so that it is normalised
    and contains as little noise as possible. The following processes are performed:
      * html special sequences are unescaped
      * unicode characters are normalised to ascii
      * the "'" character is removed
      * the token is ignored if it is a stopword or purely numeric
    """
    token = _parser.unescape(token)
    token = normalize_unicode(token)

    # Strip all punctuation from the edges of the string
    token = token.strip(punctuation)

    # Aggressively strip the following punctuation
    token = token.replace('\'', '')

    if token in _stopwords or len(token) <= 1 or isnumeric(token):
        return None
    else:
        return token


def normalize_unicode(text):
    """
    Normalize any unicode characters to ascii equivalent
    https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
    """
    if type(text) == unicode:
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
    else:
        return text


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
