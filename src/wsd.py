# encoding: utf8

from __future__ import print_function, division

import math
import numpy as np

from wikiindex import WikiIndex
from utils import load_db_params


def load_stopwords():
    # Populate custom (more comprehensive) list of stopwords
    stopwords_list = set()
    with open('data/stopwords.txt', 'r') as fp:
        while True:
            line = fp.readline()
            if line:
                stopwords_list.add(line.rstrip())
            else:
                return stopwords_list


def dump_results(path, results, terms, query_vector):

    from numpy.linalg import norm

    with open(path, 'w') as fp:
        fp.write('===Query Vector=== (weight=1.0, norm=%f, distance=0)\n' % norm(query_vector))
        for term, weight in zip(terms, query_vector):
            fp.write('%s: %f, ' % (term, weight))
        fp.write('\n\n')

        for index, (sr) in enumerate(results):
            distance = math.sqrt(np.sum((query_vector - sr.vector) ** 2))
            fp.write(
                '===%s=== (weight=%f, norm=%f, distance=%f, page_id=%d, from=%s, to=%s)\n' % (
                    sr.page_name, sr.weight,
                    norm(sr.vector), distance, sr.page_id,
                    sr.links_from, sr.links_to
                )
            )
            for term, weight in zip(terms, sr.vector):
                fp.write('%s: %f, ' % (term, weight))
            fp.write('\n\n')


def search_for(page_id, results):
    for sr in results:
        if sr.page_name == page_id:
            return sr


if __name__ == '__main__':

    import time

    from goose import Goose

    params = load_db_params('wsd.db.json')

    if not params:
        raise ValueError('Could not load database parameters')

    wiki = WikiIndex(**params)

    start_time = time.time()

    import requests
    req = requests.get('http://crsmithdev.com/arrow/')
    html_text = req.text

    print('Extracting article...')

    t0 = time.time()
    goose = Goose()
    article = goose.extract(raw_html=html_text)
    print('Extraction took %f seconds' % (time.time() - t0))

    print('===%s===' % article.title)
    print(article.cleaned_text)
    print('(%d length)' % len(article.cleaned_text))

    print(article.cleaned_text.lower().count('python'))

    print('Running word concepts....')

    t1 = time.time()
    results, terms, query_vector = wiki.word_concepts(article.cleaned_text, n=20)
    print('Word Concepts Runtime = {}'.format(time.time() - t1))

    dump_results('/home/michaela/target.vector', results, terms, query_vector)

    t2 = time.time()
    wiki.second_order_ranking(results, alpha=0.7)
    print('Second Order Runtime = {}'.format(time.time() - t2))

    print(results[:20])

    print('Runtime = {}'.format(time.time() - start_time))

    wiki.close()
