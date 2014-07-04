#! /usr/bin/python
# ~*~ coding: utf-8 ~*~
from __future__ import division

import os
import nltk
import numpy as np

import textparser

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

    if token in _stopwords or len(token) <= 1 or textparser.isnumeric(token):
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
    force_reindex = False
    parameters = {
        'samples': 900,
        'subreddit': 'python',
        'min_frequency': 0.09,
        'max_frequency': 1.00,
        'stemmer': str(_stemmer),
        'mode': 'tfidf',
    }

    print parameters
    print 'Available pages: ', len(list(search_files(os.path.join(data_path, 'pages'))))

    sr_index = HashedIndex()

    # Possible to initially just load meta-data?
    meta = sr_index.load(save_path, compressed=True)

    if force_reindex or meta['parameters'] != parameters:
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
    print 'Unlabelled: ', np.sum(y == 0)
    print 'Positive: ', np.sum(y == 1)

    from sklearn.cross_validation import StratifiedKFold
    from sklearn.metrics import *

    n = 4  # Number of folds

    kf = StratifiedKFold(y, n_folds=n)
    accuracy = np.zeros(n)
    precision = np.zeros(n)
    recall = np.zeros(n)
    f1 = np.zeros(n)
    cm = np.zeros((2, 2))

    # SVM
    # Note: Optimised values of C are data-dependent and cannot be set
    # with some pre-determined value. They need to be optimised with a
    # cross validation study in order to make the most use of them.

    classifier = None
    for index, (train, test) in enumerate(kf):
        from sklearn.svm import SVC
        classifier = SVC(kernel='linear', C=1.0)

        classifier.fit(X[train], y[train])
        y_pred = classifier.predict(X[test])

        # Store the measures obtained
        accuracy[index] = accuracy_score(y[test], y_pred)
        precision[index] = precision_score(y[test], y_pred)
        recall[index] = recall_score(y[test], y_pred)
        f1[index] = f1_score(y[test], y_pred)

        cm += confusion_matrix(y[test], y_pred)

    # Average scores across the K folds
    print
    print 'Performance Metrics'
    print '-------------------'
    print '(Using %s)' % str(classifier)
    print 'Accuracy: ', accuracy.mean()
    print 'Precision: ', precision.mean()
    print 'Recall: ', recall.mean()
    print 'F1: ', recall.mean()

    print
    print 'Confusion Matrix'
    print '----------------'
    print '(Unlabelled vs Positive)'
    print cm
