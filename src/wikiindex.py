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

# TODO: Safer SQL queries when using lists as parameters


class SearchResult(object):

    def __init__(self, page_id, page_name, vector, weight):
        self.page_id = page_id
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
        self._cur = self.connection.cursor(cursorclass=MySQLdb.cursors.Cursor)
        self._sscur = self.connection.cursor(cursorclass=MySQLdb.cursors.SSCursor)
        self._db = db
        self._host = host

    def __repr__(self):
        return '<WikiIndex %s@%s>' % (self._db, self._host)

    def close(self):
        self._cur.close()
        self._sscur.close()
        self.connection.close()

    def get_document_frequencies(self, term_id_list):
        """
        Returns a list of (TermID, DocumentFrequency)
        """
        var_string = u''
        for tid in term_id_list:
            var_string += u'%d,' % tid
        var_string = var_string[:-1]

        self._cur.execute("""
            SELECT TermID, COUNT(*)
            FROM TermOccurrences
            WHERE TermID IN (%s)
            GROUP BY TermID
        """ % var_string)
        return self._cur.fetchall()

    def get_term_ids(self, term_name_list):
        """
        Returns a list of (TermName, TermID)
        """
        var_string = u''
        for term_name in term_name_list:
            var_string += u'\'%s\',' % term_name
        var_string = var_string[:-1]

        self._cur.execute("""
            SELECT TermName, TermID
            FROM Terms
            WHERE TermName IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_page_ids(self, page_name_list):
        """
        Returns a list of (PageName, PageID)
        """
        var_string = u''
        for term_name in page_name_list:
            var_string += u'\'%s\',' % term_name
        var_string = var_string[:-1]

        self._cur.execute("""
            SELECT PageName, PageID
            FROM Pages
            WHERE PageName IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_page_links(self, page_id_list):
        """
        Returns a list of (PageID, TargetPageID, LinkCounter)
        """
        var_string = u''
        for term_name in page_id_list:
            var_string += u'\'%s\',' % term_name
        var_string = var_string[:-1]

        self._cur.execute("""
            SELECT T1.PageID, T2.PageID, T1.Counter
            FROM PageLinks T1
            INNER JOIN Pages T2 ON T1.TargetPageID = T2.PageID
            WHERE T1.PageID IN (%s);
        """ % var_string)

        return self._cur.fetchall()

    def get_documents(self, term_id, min_counter=2, limit=200):
        """
        Returns a list of (PageID, PageName, TermFrequency)
        Results are limited to the specified value and only terms
        with a Counter larger than min_counter are returned. Returned
        results are sorted in descending order by TermFrequency.
        """
        # Ordering by counter is super duper slow due to lack of index
        # and large table size (needs to perform a filesort!)
        self._cur.execute("""
            SELECT T1.PageID, T1.PageName, T2.Counter
            FROM Pages AS T1
            INNER JOIN TermOccurrences AS T2 ON T1.PageID = T2.PageID
            WHERE TermID = %s AND Counter > %s
            ORDER BY Counter DESC
            LIMIT %s;
        """, (term_id, min_counter, limit))
        return self._cur.fetchall()

    def get_corpus_size(self):
        """
        Returns the size of the corpus which excludes all unprocessed pages.
        """
        self._cur.execute('SELECT Size FROM CorpusSize;')
        (corpus, ) = self._cur.fetchone()
        self._cur.fetchall()

        return corpus

    def generate_link_matrix(self, page_id_list):
        """
        Generates a matrix containing the number of links between
        the a page (row) and a target page (column) in each cell. Only
        pages specified in the page_id_list will be included in the matrix.
        """
        size = len(page_id_list)
        link_matrix = np.zeros(shape=(size, size))

        # Build an index of page links
        page_index = dict(enumerate(page_id_list))
        page_links = self.get_page_links(page_id_list)

        for page_id, target_page_id, counter in page_links:
            if target_page_id in page_index:
                i = page_index[page_id]
                j = page_index[target_page_id]
                link_matrix[i, j] = counter

        return link_matrix

    def get_corpus_size(self):
        self.cur.execute('SELECT COUNT(*) FROM Pages WHERE Processed=1;')
        (corpus, ) = self.cur.fetchone()
        self.cur.fetchall()

        return corpus

    def get_documents(self, term_id, min_counter=2, limit=200):
        # Ordering by counter is super duper slow due to lack of index
        # and large table size (needs to perform a filesort!)
        self.cur.execute("""
            SELECT T1.PageID, T1.PageName, T2.Counter
            FROM Pages AS T1
            INNER JOIN TermOccurrences AS T2 ON T1.PageID = T2.PageID
            WHERE TermID = %s AND Counter > %s
            ORDER BY Counter DESC
            LIMIT %s
        """, (term_id, min_counter, limit))
        return self.cur.fetchall()
