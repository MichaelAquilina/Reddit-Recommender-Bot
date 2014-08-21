#! /usr/bin/python

from __future__ import print_function

import os
import json
import numpy as np

from goose import Goose, Configuration

from datasource import load_data_source
from index.wikiindex import WikiIndex
from utils import load_db_params


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Generates a community profile from a given subreddit in a Reddit Data Source')
    parser.add_argument('data_path', type=str, help='Path to a Reddit Data Source')
    parser.add_argument('output_path', type=str, help='File path for output profile')
    parser.add_argument('subreddit', type=str, help='Name of the subreddit on which to train on')
    parser.add_argument('--samples', type=int, default=600, help='Number of negative samples to use')
    parser.add_argument('--alpha', type=float, default=0.5, help='alpha parameter for second order ranking')
    parser.add_argument('--concepts', type=int, default=10, help='Number of concepts to return with each page')
    parser.add_argument('--n', type=int, default=15, help='Complexity parameter for word_concepts')

    args = parser.parse_args()

    index_path = args.output_path
    data_path = args.data_path
    pages_path = os.path.join(data_path, 'pages')

    parameters = {
        'data_path': data_path,
        'subreddit': args.subreddit,
        'n_samples': args.samples,
        'n': args.n,
        'm': 25,
        'alpha': args.alpha,
        'concepts': args.concepts,
    }

    perform_index = False

    if perform_index:
        print('Performing Index Operation from Scratch')

        # Goose Setup
        config = Configuration()
        config.enable_image_fetching = False
        config.use_meta_language = False
        goose = Goose(config)

        concepts = set()
        results = {}

        db_params = load_db_params('wsd.db.json')
        with WikiIndex(**db_params) as wiki:

            data_labels = load_data_source(parameters['data_path'], parameters['subreddit'], parameters['n_samples'])
            for index, (rel_path, label) in enumerate(data_labels.iteritems()):
                abs_path = os.path.join(pages_path, rel_path)
                if os.path.exists(abs_path):
                    print('%d: http://%s' % (index, rel_path[:-3]))
                    with open(abs_path, 'r') as fp:
                        html_text = fp.read()

                    article = goose.extract(raw_html=html_text)
                    print(article.title, '(%s)' % label)

                    text = article.cleaned_text

                    if len(text) > 500:
                        search_results, terms, query_vector = wiki.word_concepts(
                            text, article.title,
                            n=parameters['n'],
                            m=parameters['m'],
                            min_tfidf=0.6)

                        if search_results:
                            # wiki.second_order_ranking(search_results, alpha=parameters['alpha'])
                            results[rel_path] = [(sr.page_id, sr.weight) for sr in search_results[:parameters['concepts']]]

                            for search_result in search_results[:parameters['concepts']]:
                                concepts.add(search_result.page_id)

                            print(search_results[:parameters['concepts']])
                        else:
                            print('No word concepts returned')
                    else:
                        print('Document is of insufficient length')

                    print()

                    # Save the generated data to a JSON file
                    with open(index_path, 'w') as fp:
                        json.dump({
                            'Concepts': list(concepts),
                            'Results': results,
                            'Labels': data_labels,
                        }, fp, indent=5)
    else:
        print('Loading Previously Indexed Data')

        with open(index_path, 'r') as fp:
            loaded_data = json.load(fp)

        concepts = loaded_data['Concepts']
        results = loaded_data['Results']
        data_labels = loaded_data['Labels']

    print(len(concepts))

    # List of positive labels
    positive_labels = filter(lambda x: x[1] == parameters['subreddit'], data_labels.items())

    concepts_index = dict([(b, a) for (a, b) in enumerate(concepts)])

    shape = (len(results), len(concepts))
    print('Generating Feature Matrix: %dx%d' % shape)

    feature_matrix = np.zeros(shape=shape)
    label_vector = np.zeros(len(results))

    for i, (rel_path, page_list) in enumerate(results.iteritems()):
        label_vector[i] = 1 if data_labels[rel_path] is not None else 0

        for page_id, weight in page_list:
            j = concepts_index[page_id]
            feature_matrix[i, j] = weight

    # Statistics
    print('Positive:', np.sum(label_vector == 1))
    print('Negative:', np.sum(label_vector == 0))

    print('Running Machine Learning component...')

    from sklearn.cross_validation import StratifiedKFold
    from sklearn.metrics import *

    n = 4  # Number of folds
    print('Performing Evaluation with %d folds' % n)

    kf = StratifiedKFold(label_vector, n_folds=n)
    accuracy = np.zeros(n)
    precision = np.zeros(n)
    recall = np.zeros(n)
    f1 = np.zeros(n)
    cm = np.zeros((2, 2))  # Confusion matrix tally

    # SVM
    # Note: Optimised values of C are data-dependent and cannot be set
    # with some pre-determined value. They need to be optimised with a
    # cross validation study in order to make the most use of them.

    classifier = None
    for index, (train, test) in enumerate(kf):
        from sklearn.svm import SVC
        classifier = SVC(kernel='linear', C=1.0)
        classifier.fit(feature_matrix[train], label_vector[train])
        y_pred = classifier.predict(feature_matrix[test])

        # Store the measures obtained
        accuracy[index] = accuracy_score(label_vector[test], y_pred)
        precision[index] = precision_score(label_vector[test], y_pred)
        recall[index] = recall_score(label_vector[test], y_pred)
        f1[index] = f1_score(label_vector[test], y_pred)

        cm += confusion_matrix(label_vector[test], y_pred)

    # Average scores across the K folds
    print()
    print('Performance Metrics')
    print('-------------------')
    print('(Using %s)' % str(classifier))
    print('Accuracy: ', accuracy.mean())
    print('Precision: ', precision.mean())
    print('Recall: ', recall.mean())
    print('F1: ', recall.mean())

    print()
    print('Confusion Matrix')
    print('----------------')
    print('(Unlabelled vs Positive)')
    print(cm)
