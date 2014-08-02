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

    perform_index = False

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
            data_labels = load_data_source(data_path, 'python', 600)
            for index, (rel_path, label) in enumerate(data_labels.iteritems()):
                abs_path = os.path.join(pages_path, rel_path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r') as fp:
                        html_text = fp.read()

                    article = goose.extract(raw_html=html_text)
                    print('%d: %s' % (index, rel_path[:-3]))
                    print(article.title)

                    text = article.cleaned_text

                    if len(text) > 50:
                        search_results, terms, query_vector = wiki.word_concepts(text, n=15)
                        wiki.second_order_ranking(search_results)

                        results[rel_path] = [sr.page_id for sr in search_results[:use_concepts]]

                        for search_result in search_results[:use_concepts]:
                            concepts.add(search_result.page_id)

                        print(search_results[:use_concepts])
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

    concepts_index = dict([(b, a) for (a, b) in enumerate(concepts)])

    print('Generating Feature Matrix')

    feature_matrix = np.zeros(shape=(len(results), len(concepts)))
    label_vector = np.zeros(len(results))

    for i, (rel_path, page_list) in enumerate(results.iteritems()):
        label_vector[i] = 1 if data_labels[rel_path] is not None else 0

        for page_id in page_list:
            j = concepts_index[page_id]
            feature_matrix[i, j] = 1  # TODO: Use weights instead!

    from sklearn.svm import SVC
    from sklearn.cross_validation import train_test_split
    from sklearn import metrics

    X_train, X_test, y_train, y_test = train_test_split(feature_matrix, label_vector)

    classifier = SVC(kernel='linear')
    classifier.fit(X_train, y_train)

    y_predict = classifier.predict(X_test)

    print(metrics.confusion_matrix(y_test, y_predict))
    print('Accuracy: ', metrics.accuracy_score(y_test, y_predict))
    print('Precision: ', metrics.precision_score(y_test, y_predict))
    print('F1 Score:', metrics.f1_score(y_test, y_predict))
