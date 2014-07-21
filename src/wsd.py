# encoding: utf8

from __future__ import print_function, division

__about__ = """
    Module which performs word sense disambiguation on terms using the Wikipedia Corpus
"""

# TODO: This should be converted into a class which takes db parameter inputs

import MySQLdb
import math
import numpy as np
import textparser

from collections import Counter
from numpy.linalg import norm
from utils import load_db_params


class SearchResult(object):

    def __init__(self, page_name, vector, weight):
        self.page_name = page_name
        self.vector = vector
        self.weight = weight

    def __repr__(self):
        return '%s: %f' % (self.page_name, self.weight)


def tfidf(tf, df, norm_factor):
    if norm_factor and df:
        return (1 + math.log(tf)) / (1 + math.log(norm_factor)) * math.log(corpus / df)
    else:
        return 0


# Should return a list of concept ids (based on the DB)
# TODO: Alot of numpy operations can probably be performed in batch for faster speeds
# Use Natural Logarithms as these tend to scale up nicely with document size
# There are a large number of ways this can be made faster
def word_concepts(text):
    tokens = Counter(textparser.word_tokenize(text, stopwords=stopwords))
    size = len(tokens)
    query_length = sum(tokens.values())

    token_lookup = {}
    pages = {}
    query = np.zeros(size)

    for i, token in enumerate(tokens.keys()):

        # TODO: Move this to one batch operation at the beginning
        cur.execute("""
            SELECT COUNT(*)
            FROM Pages
            INNER JOIN TermOccurrences ON Pages.PageID = TermOccurrences.PageID
            INNER JOIN Terms ON TermOccurrences.TermID = Terms.TermID
            WHERE TermName = %s;
        """, (token, ))

        (df, ) = cur.fetchone()

        token_lookup[token] = (i, df)

        # Calculate tfidf on the query vector
        query[i] = tfidf(tokens[token], df, 1)

        cur.execute("""
            SELECT T1.PageID, T1.PageName, T1.Length
            FROM Pages T1
            INNER JOIN TermOccurrences T2 ON T1.PageID = T2.PageID
            INNER JOIN Terms T3 ON T2.TermID = T3.TermID
            WHERE Counter > 2 AND TermName = %s
            ORDER BY Counter DESC
            LIMIT 20;
        """, (token, ))

        for page_id, page_name, page_length in cur.fetchall():
            if page_id not in pages:
                pages[page_id] = (page_id, page_name, page_length)

    # This can probably be sped up using a matrix
    document_vectors = []

    # Iterate through the retrieved pages
    for page_id, page_name, page_length in pages.values():
        cur.execute("""
            SELECT Terms.TermID, Terms.TermName, Counter
            FROM Terms
            INNER JOIN TermOccurrences ON Terms.TermID = TermOccurrences.TermID
            WHERE TermOccurrences.PageID = %s;
        """, (page_id, ))

        vector = np.zeros(size)

        for term_id, term_name, tf in cur.fetchall():
            if term_name in token_lookup:
                j, df = token_lookup[term_name]
                vector[j] = tfidf(tf, df, page_length)

        weight = np.dot(query, vector) / (norm(vector) * norm(query))

        document_vectors.append(SearchResult(page_name, vector, weight))

    document_vectors.sort(key=lambda x: x.weight, reverse=True)

    print('Query Vector')
    for weight, term in zip(query, tokens.keys()):
        print('%s: %f' % (term, weight), end=' ')
    print()

    for i in xrange(20):
        print('=======%s: %f=======' % (document_vectors[i].page_name, document_vectors[i].weight))
        for weight, term in zip(document_vectors[i].vector, tokens.keys()):
            print('%s: %f' % (term, weight), end=' ')
        print()

if __name__ == '__main__':

    import time

    params = load_db_params()

    if not params:
        raise ValueError('Could not find db.json')

    stopwords = set()
    with open('stopwords.txt', 'r') as fp:
        while True:
            line = fp.readline()
            if line:
                stopwords.add(line.rstrip())
            else:
                break

    connection = MySQLdb.connect(**params)

    # Retrieve size of Corpus N
    cur = connection.cursor(cursorclass=MySQLdb.cursors.SSCursor)
    cur.execute('SELECT COUNT(*) FROM Pages;')
    (corpus, ) = cur.fetchone()
    cur.close()

    # Prevent "commands out of sync" by re-opening a new cursor
    cur = connection.cursor(cursorclass=MySQLdb.cursors.Cursor)

    t0 = time.time()
    # Excerpt from the following html page:
    # http://arstechnica.com/security/2014/07/ghcqs-chinese-menu-of-tools-spread-disinformation-across-internet/
    # word_concepts("""
    #     The original open source software “Benevolent Dictator For Life” and author of Python, Guido van Rossum,
    #     is leaving Google to join Dropbox, the startup will announce later today. Van Rossum was a software
    #     engineer at Google since 2005, and should be a huge help as Dropbox is built on Python. He’s the latest
    #     big hire by the cloud storage startup that’s capitalizing on its 100 million-user milestone.
    # """)
    word_concepts("""
        What appears to be an internal Wiki page detailing the cyber-weaponry used by the British spy agency
        GCHQ was published today by Glenn Greenwald of The Intercept. The page, taken from the documents
        obtained by former NSA contractor Edward Snowden, lists dozens of tools used by GCHQ to target
        individuals and their computing devices, spread disinformation posing as others, and “shape” opinion
        and information available online.

        The page had been maintained by GCHQ’s Joint Threat Research Intelligence Group (JTRIG) Covert Internet
        Technical Development team, but it fell out of use by the time Snowden copied it. Greenwald and NBC
        previously reported on JTRIG’s “dirty tricks” tactics for psychological operations and information
        warfare, and the new documents provide a hint at how those tactics were executed. GCHQ’s capabilities
        included tools for manipulating social media, spoofing communications from individuals and groups,
        and warping the perception of content online through manipulation of polls and web pages’ traffic
        and search rankings.
    """)

    print('Runtime = {}'.format(time.time() - t0))

    cur.close()
    connection.close()
