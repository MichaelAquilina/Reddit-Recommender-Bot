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

if __name__ == '__main__':

    import logging
    logging.basicConfig(format='%(message)s')
    logging.getLogger().setLevel(logging.INFO)

    db_params = load_db_params('wsd.db.json')
    wiki = WikiIndex(**db_params)

    print(wiki)

    # Constants that should become parameters
    subreddit = 'python'
    data_path = '/home/michaela/Development/Reddit-Testing-Data'
    samples = 600
    seed = 0
    n_folds = 6
    parameter = 'r'
    parameter_values = np.arange(10, 70, 5)

    x = []  # Recall
    y = []  # Precision

    if not os.path.exists('.cache'):
        os.mkdir('.cache')

    # Load appropriate pages from data source
    data = load_data_source(data_path, subreddit, samples, seed, relative=False)

    for value in parameter_values:
        file_name = '.cache/%s_boc_%s=%s.json.bz2' % (subreddit, parameter, value)

        # Check if a cached version exists first
        if os.path.exists(file_name):
            print('Found a cached copy for %s=%s' % (parameter, value))
            with bz2.BZ2File(file_name, 'r') as fp:
                cache = json.load(fp)

            feature_matrix = np.asarray(cache['feature_matrix'])
            label_vector = np.asarray(cache['label_vector'])
        else:
            print('Generate feature matrix for %s=%s' % (parameter, value))
            feature_matrix, label_vector = boc.generate_feature_matrix(wiki, data, **{parameter: value})

            # Save to cache for future pre-loading
            with bz2.BZ2File(file_name, 'w') as fp:
                json.dump({
                    'feature_matrix': feature_matrix.tolist(),
                    'label_vector': label_vector.tolist(),
                }, fp)

        kf = StratifiedKFold(label_vector, n_folds=6)

        precision = np.zeros(n_folds)
        recall = np.zeros(n_folds)
        f1 = np.zeros(n_folds)

        print('Generating mean precision and recall')

        classifier = None
        for index, (train, test) in enumerate(kf):
            classifier = SVC(kernel='linear', C=0.8)
            classifier.fit(feature_matrix[train], label_vector[train])
            y_pred = classifier.predict(feature_matrix[test])

            # Store the measures obtained
            precision[index] = precision_score(label_vector[test], y_pred)
            recall[index] = recall_score(label_vector[test], y_pred)
            f1[index] = f1_score(label_vector[test], y_pred)

        x.append(recall.mean())
        y.append(precision.mean())

    wiki.close()  # Close the database connection when done

    plt.title('Precision-Recall')
    plt.plot(x, y, color='b', linewidth=2.0)
    plt.xlabel('recall')
    plt.ylabel('precision')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.show()
