# encoding: utf8

from __future__ import print_function, division

import math
import numpy as np

from index.wikiindex import WikiIndex
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
    page_ids = [sr.page_id for sr in results]

    from numpy.linalg import norm

    with open(path, 'w') as fp:
        fp.write('Vector Lengths = %d\n\n' % len(query_vector))
        fp.write('===Query Vector=== (weight=1.0, norm=%f, distance=0)\n' % norm(query_vector))
        for term, weight in zip(terms, query_vector):
            fp.write('%s: %f, ' % (term, weight))
        fp.write('\n\n')

        for index, (sr) in enumerate(results):
            distance = math.sqrt(np.sum((query_vector - sr.vector) ** 2))
            index = page_ids.index(sr.page_id)
            fp.write(
                '%d) ===%s=== (weight=%f, norm=%f, distance=%f, page_id=%d, incoming=%s, outgoing=%s)\n' % (
                    index, sr.page_name, sr.weight,
                    norm(sr.vector), distance, sr.page_id,
                    sr.incoming, sr.outgoing
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
    # req = requests.get('http://lucumr.pocoo.org/2014/8/16/the-python-i-would-like-to-see/', verify=False)
    # req = requests.get('http://torrentfreak.com/pirating-uk-student-to-be-extradited-to-the-us-120313')  # TODO
    # req = requests.get('http://arstechnica.com/information-technology/2014/02/neither-microsoft-nokia-nor-anyone-else-should-fork-android-its-unforkable?comments=1&amp;post=26199423')
    # req = requests.get('http://hynek.me/articles/python-deployment-anti-patterns')
    # req = requests.get('http://ginstrom.com/scribbles/2008/10/06/dont-overuse-classes-in-python/')
    # req = requests.get('http://maximebf.com/blog/2012/10/building-websites-in-python-with-flask')
    req = requests.get('http://peak5390.wordpress.com/2013/03/21/what-really-happened-at-pycon-2013')
    # req = requests.get('http://pyimagesearch.com/2014/01/27/hobbits-and-histograms-a-how-to-guide-to-building-your-first-image-search-engine-in-python')
    # req = requests.get('http://graph-tool.skewed.de/')
    # req = requests.get('https://www.python.org/download/releases/3.0/')
    # req = requests.get('http://sontek.net/turning-vim-into-a-modern-python-ide')
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

    def print_results(results):
        for res in results[:10]:
            print('%s (%d): %f (%d/%d)' % (res.page_name, res.page_id, res.weight, res.incoming, res.outgoing), end=', ')
        print()

    t1 = time.time()
    results, terms, query_vector = wiki.word_concepts(article.cleaned_text, n=20, min_tfidf=0.7)

    if results is None:
        print('No results were returned, the document did not contain enough information')
        import sys
        sys.exit(1)

    print('Word Concepts Runtime = {}'.format(time.time() - t1))

    print_results(results)
    dump_results('/home/michaela/target.vector', results, terms, query_vector)

    # t2 = time.time()
    # wiki.second_order_ranking(results, alpha=0.5)
    # print('Second Order Runtime = {}'.format(time.time() - t2))
    #
    # print_results(results)

    print('Runtime = {}'.format(time.time() - start_time))

    wiki.close()
