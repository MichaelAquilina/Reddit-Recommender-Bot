# encoding: utf8

from __future__ import print_function, division

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


if __name__ == '__main__':

    import time

    params = load_db_params('wsd.db.json')

    if not params:
        raise ValueError('Could not load database parameters')

    stopwords = load_stopwords()

    wiki = WikiIndex(**params)

    print(wiki)

    t0 = time.time()
    result = wiki.word_concepts("""
        The original open source software “Benevolent Dictator For Life” and author of Python, Guido van Rossum,
        is leaving Google to join Dropbox, the startup will announce later today. Van Rossum was a software
        engineer at Google since 2005, and should be a huge help as Dropbox is built on Python. He’s the latest
        big hire by the cloud storage startup that’s capitalizing on its 100 million-user milestone.
    """)

    wiki.close()

    print('Runtime = {}'.format(time.time() - t0))
