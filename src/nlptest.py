from __future__ import print_function

import os
import json
import numpy as np

from goose import Goose, Configuration

from datasource import load_data_source
from wikiindex import WikiIndex
from utils import load_db_params


if __name__ == '__main__':

    data_path = '/home/michaela/Development/Reddit-Testing-Data'
    pages_path = os.path.join(data_path, 'pages')
    index_path = '/home/michaela/concepts.json'

    parameters = {
        'data_path': '/home/michaela/Development/Reddit-Testing-Data',
        'subreddit': 'python',
        'n_samples': 800,
    }

    perform_index = True

    if perform_index:
        print('Performing Index Operation from Scratch')

        # Goose Setup
        config = Configuration()
        config.enable_image_fetching = False
        config.use_meta_language = False
        goose = Goose(config)

        use_concepts = 10
        concepts = set()
        results = {}

        params = load_db_params('wsd.db.json')
        with WikiIndex(**params) as wiki:
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
                        search_results, terms, query_vector = wiki.word_concepts(text, article.title, n=15)

                        if search_results:
                            wiki.second_order_ranking(search_results)
                            results[rel_path] = [(sr.page_id, sr.weight) for sr in search_results[:use_concepts]]

                            for search_result in search_results[:use_concepts]:
                                concepts.add(search_result.page_id)

                            print(search_results[:use_concepts])
                        else:
                            print('No word concepts returned')
                    else:
                        print('Document is of insufficient length')

                    print()
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

    positive_labels = filter(lambda x: x[1] == parameters['subreddit'], data_labels.items())

    print(len(positive_labels))
    print(len(data_labels) - len(positive_labels))

    concepts_index = dict([(b, a) for (a, b) in enumerate(concepts)])

    # TODO: Need to see what is going to be done about those documents that do not each the minimum length requirement
    # Do you try to find another example page to replace or just deal with the fallout?

    shape = (len(results), len(concepts))
    print('Generating Feature Matrix: %dx%d' % shape)

    feature_matrix = np.zeros(shape=shape)
    label_vector = np.zeros(len(results))

    for i, (rel_path, page_list) in enumerate(results.iteritems()):
        label_vector[i] = 1 if data_labels[rel_path] is not None else 0

        for page_id, weight in page_list:
            j = concepts_index[page_id]
            feature_matrix[i, j] = weight

    print('Running Machine Learning component...')

    from sklearn.cross_validation import StratifiedKFold
    from sklearn.metrics import *

    n = 4  # Number of folds

    kf = StratifiedKFold(label_vector, n_folds=n)
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
