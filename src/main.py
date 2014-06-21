#! /usr/bin/python
# ~*~ coding: utf-8 ~*~
import nltk

import matplotlib.pyplot as plt

import textparser

from sklearn import metrics
from sklearn.cross_validation import train_test_split

from redditclassifier import RedditClassifier
from utils import search_files

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
_stemmer = nltk.PorterStemmer()


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

    import os
    import time

    # TODO: make this a program input
    target_dir = '/home/michaela/Development/Reddit-Data/'

    classifier = RedditClassifier()

    print 'Loading %d files...' % len(list(search_files(os.path.join(target_dir, 'pages'))))

    t0 = time.time()
    classifier.load_data(target_dir, ['science', 'python'], process=post_process)
    X, y = classifier.generate_data()

    classifier.index.prune()

    runtime = time.time() - t0

    print 'Runtime = {}'.format(runtime)
    print X.shape
    print 'Science: ', y[y == classifier.subreddits.index('science')].size
    print 'Python: ', y[y == classifier.subreddits.index('python')].size

    print 'Performing Machine Learning'

    X_train, X_test, y_train, y_test = train_test_split(X, y)

    from sklearn.svm import SVC
    classifier = SVC(kernel='linear')
    classifier.fit(X_train, y_train)

    y_pred = classifier.predict(X_test)

    cm = metrics.confusion_matrix(y_test, y_pred)

    print cm

    print 'Accuracy: ', metrics.accuracy_score(y_test, y_pred)
    print 'Precision: ', metrics.precision_score(y_test, y_pred)
    print 'Recall: ', metrics.recall_score(y_test, y_pred)
    print 'F1 Measure: ', metrics.f1_score(y_test, y_pred)

    plt.matshow(cm)
    plt.colorbar()
    plt.show()
