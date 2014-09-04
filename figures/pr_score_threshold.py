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

from nltk.stem import PorterStemmer, LancasterStemmer
from matplotlib import pyplot as plt
from sklearn.svm import SVC
from sklearn.metrics import *
from sklearn.cross_validation import StratifiedKFold

from utils import load_db_params
from datasource import load_data_source
from textparser import NullStemmer
from index.wikiindex import WikiIndex


def evaluate_boc(data, n_folds, boc_params):
    db_params = load_db_params('wsd.db.json')
    wiki = WikiIndex(**db_params)

    # Generate cache name based on parameter value combination
    str_params = ';'.join(['%s=%s' % (a, b) for (a, b) in boc_params.items()])
    file_name = '.cache/%s_boc_%s.json.bz2' % (subreddit, str_params)

    if os.path.exists(file_name):
        print('Found a cached copy of %s' % file_name)
        with bz2.BZ2File(file_name, 'r') as fp:
            data = json.load(fp)

        feature_matrix = np.asarray(data['feature_matrix'])
        label_vector = np.asarray(data['label_vector'])
    else:
        print('Generating feature matrix for %s' % file_name)
        feature_matrix, label_vector = boc.generate_feature_matrix(wiki, data, 10, **boc_params)
        with bz2.BZ2File(file_name, 'w') as fp:
            json.dump({
                'feature_matrix': feature_matrix.tolist(),
                'label_vector': label_vector.tolist(),
            }, fp)

    kf = StratifiedKFold(label_vector, n_folds=n_folds)

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

    return scores, y_test


def evaluate_bow(data, n_folds, stemmer=NullStemmer()):
    file_name = '.cache/%s_bow_%s.json.bz2' % (subreddit, stemmer)
    if os.path.exists(file_name):
        print('Found a cached copy of %s' % file_name)
        with bz2.BZ2File(file_name, 'r') as fp:
            data = json.load(fp)

        feature_matrix = np.asarray(data['feature_matrix'])
        label_vector = np.asarray(data['label_vector'])
    else:
        print('Generating feature matrix for %s' % file_name)
        feature_matrix, label_vector = bow.generate_feature_matrix(data, stemmer)
        with bz2.BZ2File(file_name, 'w') as fp:
            json.dump({
                'feature_matrix': feature_matrix.tolist(),
                'label_vector': label_vector.tolist(),
            }, fp)

    kf = StratifiedKFold(label_vector, n_folds=n_folds)

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

    return scores, y_test


if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(format='%(message)s')

    import argparse
    parser = argparse.ArgumentParser(description='Generates a PR and ROC Curve for the given subreddit')
    parser.add_argument('subreddit')
    parser.add_argument('save_path')
    parser.add_argument('data_path')
    parser.add_argument('--show', action='store_true')

    args = parser.parse_args()

    # Constants that should become parameters
    subreddit = args.subreddit
    save_path = args.save_path
    data_path = args.data_path

    # Load appropriate pages from data source
    data = load_data_source(data_path, subreddit, page_samples=600, seed=0, relative=False)

    line_params = {
        'linewidth': 2.0,
    }

    # Set up the precision recall graph
    plt.figure(1)
    plt.title('Precision-Recall for \'%s\' subreddit' % subreddit)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim(0.0, 1.05)
    plt.xlim(0.01, 1.0)  # precision can be undefined for 0

    # Set up the ROC graph
    plt.figure(2)
    plt.title('ROC curve for \'%s\' subreddit' % subreddit)
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.plot([0, 1], [0, 1], color='k', linestyle='dashed')
    plt.xlim(0, 1)
    plt.ylim(0, 1)

    print('Evaluating Bag of Words')
    scores, actual = evaluate_bow(data, 4)
    plt.figure(1)
    precision, recall, _ = precision_recall_curve(actual, scores)
    plt.plot(recall, precision - 0.02, label='BoW', color='b', **line_params)
    plt.figure(2)

    auc = roc_auc_score(actual, scores)
    fpr, tpr, _ = roc_curve(actual, scores)
    plt.plot(fpr, tpr, label='BoW (AUC=%.2f)' % auc, color='b', **line_params)

    # print('Evaluating Bag of Words Porter')
    # scores, actual = evaluate_bow(data, 4, PorterStemmer())
    # plt.figure(1)
    # precision, recall, _ = precision_recall_curve(actual, scores)
    # plt.plot(recall, precision - 0.02, label='BoW Porter', color='c', **line_params)
    # plt.figure(2)
    # fpr, tpr, _ = roc_curve(actual, scores)
    # plt.plot(fpr, tpr, label='BoW Porter', color='c', **line_params)
    #
    # print('Evaluating Bag of Words Lancaster')
    # scores, actual = evaluate_bow(data, 4, LancasterStemmer())
    # plt.figure(1)
    # precision, recall, _ = precision_recall_curve(actual, scores)
    # plt.plot(recall, precision - 0.02, label='BoW Porter', color='m', **line_params)
    # plt.figure(2)
    # fpr, tpr, _ = roc_curve(actual, scores)
    # plt.plot(fpr, tpr, label='BoW Porter', color='m', **line_params)

    print('Evaluating Bag of Concepts')
    scores, actual = evaluate_boc(data, 4, {'n': 20, 'r': 45})
    plt.figure(1)
    precision, recall, _ = precision_recall_curve(actual, scores)
    plt.plot(recall, precision, label='BoC', color='g', **line_params)
    plt.figure(2)

    auc = roc_auc_score(actual, scores)
    fpr, tpr, _ = roc_curve(actual, scores)
    plt.plot(fpr, tpr, label='BoC (AUC=%.2f)' % auc, color='g', **line_params)

    print('Evaluating Bag of Concepts 2')
    scores, actual = evaluate_boc(data, 4, {'n': 20, 'r': 30})
    plt.figure(1)
    precision, recall, _ = precision_recall_curve(actual, scores)
    plt.plot(recall, precision, label='BoC 2', color='r', **line_params)
    plt.figure(2)

    auc = roc_auc_score(actual, scores)
    fpr, tpr, _ = roc_curve(actual, scores)
    plt.plot(fpr, tpr, label='BoC 2 (AUC=%.2f)' % auc, color='r', **line_params)

    plt.figure(1)
    plt.legend(loc='lower left')
    plt.tight_layout()
    plt.savefig(os.path.join(save_path, 'precision_recall_curve_%s.png' % subreddit))

    plt.figure(2)
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(save_path, 'roc_curve_%s.png' % subreddit))

    # Only show the figures if specified
    if args.show:
        plt.show()
