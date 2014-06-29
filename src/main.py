#! /usr/bin/python
# ~*~ coding: utf-8 ~*~
from __future__ import division

import nltk
import numpy as np

import textparser

from HTMLParser import HTMLParser
from string import punctuation

from redditclassifier import load_data_source
from hashedindex import HashedIndex


# Stemmer interface which returns token unchanged
class NullStemmer(object):

    def stem(self, x):
        return x

    def __str__(self):
        return '<NullStemmer>'

_parser = HTMLParser()
_stopwords = frozenset(nltk.corpus.stopwords.words())

# Lancaster Stemmer is very very slow
_stemmer = NullStemmer()


# Helper function that performs post-processing on tokens
# Should be an argument that can be passed
def post_process(token):
    token = _parser.unescape(token)
    token = token.lower()

    # TODO: Check if email, url, date etc...
    # Based on type you should parse accordingly
    # Try conflate things to reduce space and decrease noise

    token = textparser.normalize_unicode(token)

    # Strip all punctuation from the edges of the string
    token = token.strip(punctuation)

    # Aggressively strip the following punctuation
    token = token.replace('\'', '')

    if token in _stopwords:
        return None
    else:
        return _stemmer.stem(token)


if __name__ == '__main__':

    import time
    t0 = time.time()

    data_path = '/home/michaela/Development/Reddit-Testing-Data'
    save_path = '/home/michaela/Development/python_sr.json.bz2'
    python_sr = HashedIndex()

    data = load_data_source(python_sr, data_path, subreddit='python', page_samples=800, process=post_process)

    print 'Original shape: (%d, %d)' % (len(python_sr.documents()), len(python_sr.terms()))

    # Values larger than 0.01 for min_frequency can be considered "aggressive" pruning
    python_sr.prune(min_frequency=0.08)
    python_sr.save(save_path, compressed=True, stemmer=str(_stemmer), subreddit='python')

    # python_sr.load(save_path, compressed=True)

    # Generate numpy feature matrix
    X = python_sr.generate_feature_matrix(mode='tfidf')

    # TODO: Move the generator code below to a function
    y = np.zeros(len(python_sr.documents()))
    for index, doc in enumerate(python_sr.documents()):
        y[index] = 0 if data[doc] is None else 1

    print y
    print y.shape
    print np.sum(y == 1)
    print np.sum(y == 0)

    print 'Pruned shape: (%d, %d)' % X.shape
    print 'Runtime: {}'.format(time.time() - t0)
