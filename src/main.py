#! /usr/bin/python
# ~*~ coding: utf-8 ~*~
from __future__ import division

import os
import nltk
import numpy as np

import textparser

from sklearn import metrics
from sklearn.cross_validation import train_test_split
from HTMLParser import HTMLParser
from string import punctuation

from datasource import load_data_source
from hashedindex import HashedIndex
from utils import search_files


# Stemmer interface which returns token unchanged
class NullStemmer(object):

    def stem(self, x):
        return x

    def __str__(self):
        return '<NullStemmer>'

_parser = HTMLParser()
_stopwords = frozenset(nltk.corpus.stopwords.words())


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

    # Lancaster Stemmer is very very slow
    _stemmer = NullStemmer()

    data_path = '/home/michaela/Development/Reddit-Testing-Data'
    save_path = '/home/michaela/Development/python_sr.json.bz2'

    # Set the parameters to the program over here
    force_load = False
    parameters = {
        'samples': 900,
        'subreddit': 'python',
        'min_frequency': 0.08,
        'max_frequency': 1.00,
        'stemmer': str(_stemmer),
        'mode': 'tfidf',
    }

    print 'Available pages: ', len(list(search_files(os.path.join(data_path, 'pages'))))

    sr_index = HashedIndex()

    # Possible to initially just load meta-data?
    meta = sr_index.load(save_path, compressed=True)

    if force_load or meta['parameters'] != parameters:
        print 'State File Parameters out of date. Re-Indexing...'

        sr_index.clear()
        data = load_data_source(sr_index, data_path, subreddit=parameters['subreddit'], page_samples=parameters['samples'], preprocess=post_process)

        print 'Original shape: (%d, %d)' % (len(sr_index.documents()), len(sr_index.terms()))

        # Values larger than 0.01 for min_frequency can be considered "aggressive" pruning
        sr_index.prune(min_frequency=parameters['min_frequency'], max_frequency=parameters['max_frequency'])
        sr_index.save(save_path, compressed=True, text_class=data, parameters=parameters)
    else:
        print 'State File is up to date'
        data = meta['text_class']

    # Generate numpy feature matrix
    print 'Generating feature matrix'

    t1 = time.time()
    X = sr_index.generate_feature_matrix(mode=parameters['mode'])
    sr_index.freeze()  # Prevent more terms from being added

    print 'generation runtime = {}'.format(time.time() - t1)

    print 'Feature Matrix shape: (%d, %d)' % X.shape
    print 'Runtime: {}'.format(time.time() - t0)

    # TODO: Move the generator code below to a function
    # This needs to be better tested, not sure if this is 100% correct
    y = np.zeros(len(sr_index.documents()))
    for index, doc in enumerate(sr_index.documents()):
        y[index] = 0 if data[doc] is None else 1

    print y
    print y.shape
    print 'Positive: ', np.sum(y == 1)
    print 'Unlabelled: ', np.sum(y == 0)

    X_train, X_test, y_train, y_test = train_test_split(X, y)

    # Machine Learning Stuff Here
    from sklearn.linear_model import SGDClassifier

    classifier = SGDClassifier()
    classifier.fit(X_train, y_train)

    y_pred = classifier.predict(X_test)

    # Print confusion matrix to understand overall performance
    cm = metrics.confusion_matrix(y_test, y_pred)
    print cm

    # Standard ML metrics
    print 'Accuracy: ', metrics.accuracy_score(y_test, y_pred)

    # Test out some pages
    import requests
    pages = [
        'http://www.cnet.com/uk/news/linux-arrives-on-loaded-dell-ultrabook/',
        'http://www.mirror.co.uk/news/uk-news/uk-average-salary-26500-figures-3002995',
        'http://www.bristolastrosoc.org.uk/www/pages/the-society.php',
        'https://www.dlitz.net/software/pycrypto/',  # Python
        'http://jakevdp.github.io/blog/2013/07/10/XKCD-plots-in-matplotlib/',  # Python
        'http://jakevdp.github.io/blog/2012/10/07/xkcd-style-plots-in-matplotlib/',  # Python
    ]

    for p in pages:

        req = requests.get(p)

        text = nltk.clean_html(req.text)
        for token in textparser.word_tokenize(text, remove_case=True):
            # Handle "or" case represented by "/"
            for split_token in token.split('/'):
                post_processed_token = post_process(split_token)
                if post_processed_token:
                    sr_index.add_term_occurrence(post_processed_token, p)

        doc_vector = sr_index.generate_document_vector(p)

        print '%s: %s' % (p, classifier.predict(doc_vector))
