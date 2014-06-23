#! /usr/bin/python
# ~*~ coding: utf-8 ~*~
import nltk

import textparser

from redditclassifier import RedditClassifier

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

    from scipy import sparse
    from sklearn.svm import SVC
    from sklearn import metrics
    from sklearn.cross_validation import train_test_split

    # TODO: make this a program input
    target_dir = '/home/michaela/Development/Reddit-Data/'

    reddit = RedditClassifier()

    # Load Data Source
    reddit.load_data_source(target_dir, subreddits=['science', 'python'], process=post_process)
    reddit.index.prune()

    # Save for future pre-loading
    reddit.save('/home/michaela/reddit.json.bz2', compressed=True)

    # Generate feature matrix and label vector
    X, y = reddit.generate_data()
    X_csr = sparse.csr_matrix(X)
    X_train, X_test, y_train, y_test = train_test_split(X_csr, y)

    # Train
    classifier = SVC(kernel='linear')
    classifier.fit(X_train, y_train)

    # Predict unseen instances
    y_pred = classifier.predict(X_test)

    # evaluate performance on unseen instances
    cm = metrics.confusion_matrix(y_test, y_pred)
    print cm

    print 'Accuracy: ', metrics.accuracy_score(y_test, y_pred)
    print 'Recall: ', metrics.recall_score(y_test, y_pred)
    print 'Precision: ', metrics.precision_score(y_test, y_pred)
    print 'F1 Measure: ', metrics.f1_score(y_test, y_pred)
