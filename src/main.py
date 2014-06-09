#! /usr/bin/python
# ~*~ coding: utf-8 ~*~

import os
import nltk

import hashedindex
import textparser

from HTMLParser import HTMLParser
from string import punctuation

_parser = HTMLParser()
_stopwords = frozenset(nltk.corpus.stopwords.words())


# Helper function that performs post-processing on tokens
# Should probably write a test for this and move it to textparser
# TODO: Profile, this is probably going to be a major performance bottleneck
def post_process(token):
    token = _parser.unescape(token)

    # TODO: Check if email, url, date etc...
    # Based on type you should parse accordingly
    # Try conflate things to reduce space and decrease noise

    token = textparser.normalize_unicode(token)

    # Strip all punctuation from the edges of the string
    token = token.strip(punctuation)

    token = token.replace('\'', '')

    # TODO: Stemmer (Porter or Lancaster)

    if token in _stopwords:
        return None
    else:
        return token

if __name__ == '__main__':

    import time

    index = hashedindex.HashedIndex()

    target_dir = '/home/michaela/Examples'

    t0 = time.time()

    def search_dir(path):
        for p in os.listdir(path):
            abs_path = os.path.join(path, p)

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
                        post_processed_token = post_process(split_token)
                        if post_processed_token:
                            index.add_term_occurrence(post_processed_token, p)

    # Recursive search on the target directory
    search_dir(target_dir)

    runtime = time.time() - t0

    print 'Runtime = {}'.format(runtime)
    print index

    index.save('/home/michaela/index.json', compressed=False)
