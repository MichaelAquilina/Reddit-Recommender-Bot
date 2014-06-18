#! /usr/bin/python
# ~*~ coding: utf-8 ~*~

import os
import nltk
import json
import numpy as np

import hashedindex
import textparser

from url import Url

from HTMLParser import HTMLParser
from string import punctuation


# Reddit Developer API Notes
# t1_	Comment
# t2_	Account
# t3_	Link
# t4_	Message
# t5_	Subreddit
# t6_	Award
# t8_	PromoCampaign


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
        return stemmer.stem(token)


if __name__ == '__main__':

    import time

    # TODO: make this a program input
    target_dir = '/home/michaela/Development/Reddit-Data/'

    # Stores the appropriate classification for each document added
    text_classification = {}

    index = hashedindex.HashedIndex()
    stemmer = nltk.LancasterStemmer()

    pages_dir = os.path.join(target_dir, 'pages')
    subreddits_dir = os.path.join(target_dir, 'subreddits')

    subreddits = ['science', 'python']

    print 'Using the following subreddits: %s' % subreddits

    t0 = time.time()

    # Parse JSON subreddit files
    for sr in subreddits:
        sr_abs_path = os.path.join(subreddits_dir, sr)

        for json_file in os.listdir(sr_abs_path):
            with open(os.path.join(sr_abs_path, json_file)) as fp:
                post_data = json.load(fp)

            for post in post_data['data']['children']:
                if post['kind'] == 't3':    # Only interested in type 3 (link) posts
                    post_url = Url(post['data']['url'])

                    if post_url.path == '/':
                        rel_path = os.path.join(post_url.hostname, 'index.html')
                    else:
                        rel_path = os.path.join(post_url.hostname, post_url.path.lstrip('/'))

                    if post_url.query:
                        rel_path += '?' + post_url.query

                    abs_path = os.path.join(pages_dir, rel_path)

                    if os.path.exists(abs_path):
                        print '%s : %s' % (sr, rel_path)

                        with open(abs_path, 'r') as html_file:
                            html_text = html_file.read()

                        # This currently provides good accuracy but does not
                        # handle html tags very well
                        text = nltk.clean_html(html_text)

                        for token in textparser.word_tokenize(text, remove_case=True):

                            # Handle "or" case represented by "/"
                            for split_token in token.split('/'):
                                post_processed_token = post_process(split_token, stemmer=stemmer)
                                if post_processed_token:
                                    text_classification[rel_path] = sr
                                    index.add_term_occurrence(post_processed_token, rel_path)

    runtime = time.time() - t0

    print 'Runtime = {}'.format(runtime)
    print index

    t0 = time.time()
    feature_matrix = index.generate_feature_matrix(mode='tfidf')
    runtime = time.time() - t0

    print 'Feature matrix shape = {}'.format(feature_matrix.shape)
    print feature_matrix
    print 'Runtime = {}'.format(runtime)

    # Generate the label vector
    label_vector = np.zeros((len(index.documents())))
    for i, document in enumerate(index.documents()):
        label_vector[i] = subreddits.index(text_classification[document])

    print 'Label vector shape = {}'.format(label_vector.shape)
    print label_vector
    print 'Python = ', label_vector[label_vector == subreddits.index('python')].size
    print 'Science = ', label_vector[label_vector == subreddits.index('science')].size

    index.save('/home/michaela/index.json.bz2', compressed=True, comment='Using {}'.format(stemmer))
