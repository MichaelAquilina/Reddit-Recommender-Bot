"""
Module to perform feature generation using the Bag of Concepts model.
"""

import os
import logging
import numpy as np

from goose import Goose, Configuration


def generate_feature_matrix(wiki, data, n_concepts=10, **word_concept_params):
    """
    Transforms a given data source to a corresponding feature matrix and label
    vector based on the "Bag of Concepts" model which uses Wikipedia as an
    exogenous knowledge source for Word Sense Disambiguation and as additional
    domain knowledge.

    Contains logging code which is displayed depending on the currently set
    logging level of the root logger.
    :param wiki: WikiIndex instance to some database index
    :param data: data labels loaded using a load_data_source method
    :param n_concepts: number of concepts to use per page.
    :param word_concept_params: word concept parameters to use for generation of concepts.
    :return: Numpy Feature Matrix and Label Vector.
    """

    config = Configuration()
    config.enable_image_fetching = False
    config.use_meta_language = False
    goose = Goose(config)

    results = {}
    concepts = set()

    # Iterate through the data and perform training
    for index, (abs_path, label) in enumerate(data.items()):
        if not os.path.exists(abs_path):
            continue

        with open(abs_path, 'r') as fp:
            html_text = fp.read()

        # Determine relative path using a simple heuristic
        cutoff = abs_path.find('pages/')
        rel_path = abs_path[cutoff + 6:]

        logging.info('\n%d: http://%s' % (index, rel_path[:-3]))
        article = goose.extract(raw_html=html_text)

        if len(article.cleaned_text) > 500:
            logging.info('%s (%s)', article.title, label)

            search_results, terms, query_vector = wiki.word_concepts(article.cleaned_text, article.title, **word_concept_params)

            if search_results:
                results[abs_path] = [(sr.page_id, sr.weight) for sr in search_results[:n_concepts]]

                # Remove any concepts which have a weight of 0
                results[abs_path] = filter(lambda x: x[1] > 0, results[abs_path])

                for search_result in search_results[:n_concepts]:
                    concepts.add(search_result.page_id)

                logging.info(search_results[:n_concepts])
            else:
                logging.warn('No word concepts returned')
        else:
            logging.info('Document is of insufficient length')

    shape = (len(results), len(concepts))

    concepts_index = dict([(b, a) for (a, b) in enumerate(concepts)])

    feature_matrix = np.zeros(shape=shape)
    label_vector = np.zeros(len(results))

    for i, (abs_path, page_list) in enumerate(results.iteritems()):
        label_vector[i] = 1 if data[abs_path] is not None else 0

        for page_id, weight in page_list:
            j = concepts_index[page_id]
            feature_matrix[i, j] = weight

    return feature_matrix, label_vector
