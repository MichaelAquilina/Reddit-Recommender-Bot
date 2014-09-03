import os
from HTMLParser import HTMLParser
import numpy as np

from goose import Goose, Configuration
from textparser import word_tokenize
from index.hashedindex import HashedIndex


def generate_feature_matrix(data, stemmer, **prune_params):
    config = Configuration()
    config.enable_image_fetching = False
    config.use_meta_language = False
    goose = Goose(config)

    _parser = HTMLParser()

    sr_index = HashedIndex()

    for url_path, label in data.items():

        if os.path.exists(url_path):
            with open(url_path, 'r') as html_file:
                html_text = html_file.read()

            text = unicode(goose.extract(raw_html=html_text).cleaned_text)
            text = _parser.unescape(text)

            for token in word_tokenize(text, stemmer=stemmer):
                sr_index.add_term_occurrence(token, url_path)

    sr_index.prune(**prune_params)

    X = sr_index.generate_feature_matrix(mode='tfidf')

    y = np.zeros(len(sr_index.documents()))
    for index, doc in enumerate(sr_index.documents()):
        y[index] = 0 if data[doc] is None else 1

    return X, y
