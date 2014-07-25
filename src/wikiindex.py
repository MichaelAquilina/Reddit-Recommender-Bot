from __future__ import division

"""
Utility file used to perform typical queries on the Wikipedia Index
"""
import math
import MySQLdb
import numpy as np

from numpy.linalg import norm
from collections import Counter

from textparser import word_tokenize


# Determining the best way to calculate tfidf is proving difficult, might need more advanced techniques
def tfidf(tf, df, norm_factor, corpus_size):
    if norm_factor and df:
        return (1 + math.log(tf)) / (1 + math.log(norm_factor)) * math.log(corpus_size / df)
    else:
        return 0


class SearchResult(object):

    def __init__(self, page_name, vector, weight):
        self.page_name = page_name
        self.vector = vector
        self.weight = weight

    def __repr__(self):
        return '%s: %f' % (self.page_name, self.weight)


class WikiIndex(object):
    """
    Contains numerous utility methods aimed at providing information about the currently
    selected Wikipedia Index. See Github for specifications about the database design.
    """

    def __init__(self, user, passwd, host, db):
        self.connection = MySQLdb.connect(user=user, passwd=passwd, host=host, db=db)
        self.cur = self.connection.cursor(cursorclass=MySQLdb.cursors.Cursor)

    def close(self):
        self.cur.close()
        self.connection.close()

    def get_document_frequency(self, term):
        self.cur.execute("""
            SELECT COUNT(*)
            FROM Terms
            WHERE TermName=%s;
        """, (term, ))
        (df, ) = self.cur.fetchone()
        self.cur.fetchall()

        return df

    def get_page_id(self, page_name):
        self.cur.execute("""
            SELECT PageID
            FROM Pages
            WHERE PageName=%s;
        """, (page_name, ))
        (page_id, ) = self.cur.fetchone()
        self.cur.fetchall()
        return page_id

    def get_page_links(self, page_id):
        self.cur.execute("""
            SELECT T2.PageID, T2.PageName, T1.Counter
            FROM PageLinks T1
            INNER JOIN Pages T2 ON T1.TargetPageID = T2.PageID
            WHERE T1.PageID = %s;
        """, (page_id, ))

        return self.cur.fetchall()

    def generate_link_matrix(self, page_id_list):
        size = len(page_id_list)
        link_matrix = np.zeros(shape=(size, size))

        # Build an index of page links
        page_index = dict([(page_id, index) for index, page_id in enumerate(page_id_list)])

        for i, page_id in enumerate(page_id_list):
            for target_page_id, target_page_name, counter in self.get_page_links(page_id):
                if target_page_id in page_index:
                    j = page_index[target_page_id]
                    link_matrix[i, j] = math.log(counter)

        return link_matrix

    def get_corpus_size(self):
        self.cur.execute('SELECT COUNT(*) FROM Pages WHERE Processed=1;')
        (corpus, ) = self.cur.fetchone()
        self.cur.fetchall()

        return corpus
