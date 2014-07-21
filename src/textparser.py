import re
import nltk
import unicodedata

from copy import copy
from string import ascii_letters, whitespace, digits, punctuation
from HTMLParser import HTMLParser


# Stemmer interface which returns token unchanged
class NullStemmer(object):

    def stem(self, x):
        return x

    def __str__(self):
        return '<NullStemmer>'

_parser = HTMLParser()
_stopwords = frozenset(nltk.corpus.stopwords.words('english'))
_accepted = frozenset(ascii_letters + digits + punctuation) - frozenset('\'')

_punctuation = copy(punctuation)
_punctuation = _punctuation.replace('\\', '')
_punctuation = _punctuation.replace('/', '')
_punctuation = _punctuation.replace('-', '')

_re_punctuation = re.compile('[%s]' % re.escape(_punctuation))
_re_token = re.compile(r'[a-z0-9]+')

_url_pattern = r'(https?:\/\/)?(([\da-z-]+)\.){1,2}.([a-z\.]{2,6})(/[\/\w \.-]*)*\/?'
_re_full_url = re.compile(r'^%s$' % _url_pattern)
_re_url = re.compile(_url_pattern)


def normalize_unicode(text):
    """
    Normalize any unicode characters to ascii equivalent
    https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
    """
    if type(text) == unicode:
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
    else:
        return text


def word_tokenize(text, stopwords=_stopwords, remove_urls=False):
    """
    Parses the given text and yields tokens which represent words within
    the given text. Tokens are assumed to be divided by any form of
    whitespace character.
    """
    if remove_urls:
        text = re.sub(_re_url, '', text)

    text = re.sub(_re_punctuation, '', text)

    for token in re.findall(_re_token, text.lower()):
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


def is_url(text):
    """
    Returns a True if the text is a url and False otherwise.
    """
    return bool(_re_full_url.match(text))
