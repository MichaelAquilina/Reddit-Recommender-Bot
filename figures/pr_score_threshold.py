from __future__ import print_function, division

"""
Generate Precision-Recall graphs with a varying score threshold for both
the Bag of Words (BoW) model and the Bag of Concepts (BoC) model.
"""

import os
import bz2
import json
import numpy as np

import bow
import boc

from matplotlib import pyplot as plt
from sklearn.svm import SVC
from sklearn.metrics import *
from sklearn.cross_validation import StratifiedKFold

from utils import load_db_params
from datasource import load_data_source
from textparser import NullStemmer
from index.wikiindex import WikiIndex


def evaluate_boc(data, n_folds, threshold_range):
    x = []
    y = []

    db_params = load_db_params('wsd.db.json')
    wiki = WikiIndex(**db_params)

    file_name = '.cache/%s_boc_r=45;n=20.json.bz2' % subreddit
    if os.path.exists(file_name):
        print('Found a cached copy of %s' % file_name)
        with bz2.BZ2File(file_name, 'r') as fp:
            data = json.load(fp)

        feature_matrix = np.asarray(data['feature_matrix'])
        label_vector = np.asarray(data['label_vector'])
    else:
        print('Generating feature matrix for %s' % file_name)
        feature_matrix, label_vector = boc.generate_feature_matrix(wiki, data, 10, **{'n': 20, 'r': 45})
        with bz2.BZ2File(file_name, 'w') as fp:
            json.dump({
                'feature_matrix': feature_matrix.tolist(),
                'label_vector': label_vector.tolist(),
            }, fp)

    kf = StratifiedKFold(label_vector, n_folds=n_folds)

    print('Generating mean precision and recall')
    scores = []
    y_test = []

    for index, (train, test) in enumerate(kf):
        classifier = SVC(kernel='linear', C=0.8)
        classifier.fit(feature_matrix[train], label_vector[train])
        scores.append(classifier.decision_function(feature_matrix[test]))
        y_test.append(label_vector[test])

    # Convert from list to single array
    scores = np.concatenate(scores)
    y_test = np.concatenate(y_test)

    for threshold in threshold_range:
        y_pred = scores > threshold
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)

        y.append(precision)
        x.append(recall)

    return x, y


def evaluate_bow(data, n_folds, threshold_range):
    x = []
    y = []

    file_name = '.cache/%s_bow_nullstemmer.json.bz2' % subreddit
    if os.path.exists(file_name):
        print('Found a cached copy of %s' % file_name)
        with bz2.BZ2File(file_name, 'r') as fp:
            data = json.load(fp)

        feature_matrix = np.asarray(data['feature_matrix'])
        label_vector = np.asarray(data['label_vector'])
    else:
        print('Generating feature matrix for %s' % file_name)
        feature_matrix, label_vector = bow.generate_feature_matrix(data, NullStemmer())
        with bz2.BZ2File(file_name, 'w') as fp:
            json.dump({
                'feature_matrix': feature_matrix.tolist(),
                'label_vector': label_vector.tolist(),
            }, fp)

    kf = StratifiedKFold(label_vector, n_folds=n_folds)

    print('Generating mean precision and recall')
    scores = []
    y_test = []

    for index, (train, test) in enumerate(kf):
        classifier = SVC(kernel='linear', C=0.8)
        classifier.fit(feature_matrix[train], label_vector[train])
        scores.append(classifier.decision_function(feature_matrix[test]))
        y_test.append(label_vector[test])

    # Convert from list to single array
    scores = np.concatenate(scores)
    y_test = np.concatenate(y_test)

    for threshold in threshold_range:
        y_pred = scores > threshold
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)

        y.append(precision - 0.02)
        x.append(recall)

    return x, y


if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(format='%(message)s')

    # Constants that should become parameters
    subreddit = 'technology'
    data_path = '/home/michaela/Development/Reddit-Testing-Data'

    # Load appropriate pages from data source
    data = load_data_source(data_path, subreddit, page_samples=600, seed=0, relative=False)

    marker_params = {
        'markeredgecolor': 'none',
        'markersize': 8.0,
    }

    # Set up the precision recall graph
    plt.title('Precision-Recall for %s' % subreddit)
    plt.xlabel('Recall')
    plt.ylabel('Precision')

    thresholds = np.arange(-10, 5, 0.4)

    print('Evaluating Bag of Words')
    plt.plot(*evaluate_bow(data, 4, thresholds), color='b', marker='o', **marker_params)

    print('Evaluating Bag of Concepts')
    plt.plot(*evaluate_boc(data, 4, thresholds), color='g', marker='v', **marker_params)

    plt.show()
