from __future__ import division, print_function

import os
import bz2
import json
import numpy as np

import boc

from matplotlib import pyplot as plt
from sklearn.svm import SVC
from sklearn.cross_validation import StratifiedKFold
from sklearn.metrics import *

from index.wikiindex import WikiIndex
from utils import load_db_params
from datasource import load_data_source


def get_parameter_combinations(parameters):
    # Iterate through all possible parameter combinations
    current = {}
    parameters_index = {}
    varying_index = 0

    while True:
        # Only break when all possible combinations have been exhausted
        if varying_index >= len(parameters):
            return

        # determine current parameter combination
        for i, p in enumerate(parameters.keys()):
            j = parameters_index.get(p, 0)
            current[p] = parameters[p][j]

            if i == varying_index:
                if j + 1 < len(parameters[p]):
                    j += 1
                else:
                    varying_index += 1

            parameters_index[p] = j
        yield current


def evaluate_boc(data, parameters, n_folds):
    db_params = load_db_params('wsd.db.json')
    wiki = WikiIndex(**db_params)

    x = []  # Recall
    y = []  # Precision

    if not os.path.exists('.cache'):
        os.mkdir('.cache')

    for key_values in get_parameter_combinations(parameters):

        # Generate cache name based on parameter value combination
        str_params = ';'.join(['%s=%s' % (a, b) for (a, b) in key_values.items()])
        file_name = '.cache/%s_boc_%s.json.bz2' % (subreddit, str_params)

        # Check if a cached version exists first
        if os.path.exists(file_name):
            print('Found a cached copy for %s' % str_params)
            with bz2.BZ2File(file_name, 'r') as fp:
                cache = json.load(fp)

            feature_matrix = np.asarray(cache['feature_matrix'])
            label_vector = np.asarray(cache['label_vector'])
        else:
            print('Generate feature matrix for %s' % str_params)
            feature_matrix, label_vector = boc.generate_feature_matrix(wiki, data, **key_values)

            # Save to cache for future pre-loading
            with bz2.BZ2File(file_name, 'w') as fp:
                json.dump({
                    'feature_matrix': feature_matrix.tolist(),
                    'label_vector': label_vector.tolist(),
                }, fp)

        kf = StratifiedKFold(label_vector, n_folds=n_folds)

        precision = np.zeros(n_folds)
        recall = np.zeros(n_folds)
        f1 = np.zeros(n_folds)

        print('Generating mean precision and recall')

        for index, (train, test) in enumerate(kf):
            classifier = SVC(kernel='linear', C=0.8)
            classifier.fit(feature_matrix[train], label_vector[train])
            y_pred = classifier.predict(feature_matrix[test])

            # Store the measures obtained
            precision[index] = precision_score(label_vector[test], y_pred)
            recall[index] = recall_score(label_vector[test], y_pred)
            f1[index] = f1_score(label_vector[test], y_pred)

        print('Precision', precision.mean())
        print('Recall', recall.mean())

        x.append(round(recall.mean(), 2))
        y.append(round(precision.mean(), 2))

    wiki.close()  # Close the database connection when done*

    return x, y

if __name__ == '__main__':

    import logging
    logging.basicConfig(format='%(message)s')
    logging.getLogger().setLevel(logging.INFO)

    # Dictionary of parameters which may vary
    parameters = {
        'n': (20, ),
        'r': np.arange(10, 60, 5)
    }

    # Constants that should become parameters
    subreddit = 'python'
    data_path = '/home/michaela/Development/Reddit-Testing-Data'

    # Load appropriate pages from data source
    data = load_data_source(data_path, subreddit, page_samples=600, seed=0, relative=False)

    x, y = evaluate_boc(data, parameters, n_folds=4)

    plt.title('Precision-Recall for BoC')
    plt.plot(x, y, color='b', linewidth=2.0, marker='o', markeredgecolor='none', markersize=8.0)
    plt.xlabel('recall')
    plt.ylabel('precision')
    plt.show()
