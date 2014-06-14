#! /usr/bin/python
# ~*~ coding: utf-8 ~*~

import os
import nltk

import hashedindex
import textparser

from HTMLParser import HTMLParser
from string import punctuation


# Stemmer interface which returns token unchanged
class NullStemmer(object):

    def stem(self, x):
        return x

    def __str__(self):
        return '<NullStemmer>'

_parser = HTMLParser()
_stopwords = frozenset(nltk.corpus.stopwords.words())


# Helper function that performs post-processing on tokens
def post_process(token, stemmer):
    token = _parser.unescape(token)

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
        return stemmer.stem(token)

if __name__ == '__main__':

    import time
    from pympler.asizeof import asizeof

    index = hashedindex.HashedIndex()
    stemmer = NullStemmer()

    target_dir = '/home/michaela/Examples'

    t0 = time.time()

    def search_dir(path):
        for p in os.listdir(path):
            abs_path = os.path.join(path, p)
            rel_path = os.path.relpath(abs_path, target_dir)

            # Depth-First-Search
            if os.path.isdir(abs_path):
                search_dir(abs_path)
            else:
                with open(abs_path, 'r') as fp:
                    html_text = fp.read()

                # This currently provides good accuracy but does not
                # handle html tags very well
                text = nltk.clean_html(html_text)

                for token in textparser.word_tokenize(text, remove_case=True):

                    # Handle "or" case represented by "/"
                    for split_token in token.split('/'):
                        post_processed_token = post_process(split_token, stemmer=stemmer)
                        if post_processed_token:
                            index.add_term_occurrence(post_processed_token, rel_path)

    # Recursive search on the target directory
    search_dir(target_dir)

    runtime = time.time() - t0

    print 'Runtime = {}'.format(runtime)
    print index

    print 'HashedIndex size = {}'.format(asizeof(index))

    t0 = time.time()
    feature_matrix = index.generate_feature_matrix(mode='tfidf')

    print feature_matrix
    print 'Feature matrix size = {}'.format(asizeof(feature_matrix))

    runtime = time.time() - t0
    print 'Runtime = {}'.format(runtime)

    index.save('/home/michaela/index.json', compressed=False, comment='Using {}'.format(stemmer))
