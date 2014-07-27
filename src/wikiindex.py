from __future__ import division

import MySQLdb
import numpy as np

from numpy.linalg import norm
from collections import Counter

from utils import to_csv
from textparser import word_tokenize, tfidf

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
        var_string = to_csv(term_id_list)

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
        var_string = to_csv(term_name_list)

        self._cur.execute("""
            SELECT TermName, TermID
            FROM Terms
            WHERE TermName IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_term_names(self, term_id_list):
        """
        Returns a list of (TermID, TermName)
        """
        var_string = to_csv(term_id_list)

        self._cur.execute("""
            SELECT TermID, TermName
            FROM Terms
            WHERE TermID IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_page_ids(self, page_name_list):
        """
        Returns a list of (PageName, PageID)
        """
        var_string = to_csv(page_name_list)

        self._cur.execute("""
            SELECT PageName, PageID
            FROM Pages
            WHERE PageName IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_page_names(self, page_id_list):
        """
        Returns a list of (PageID, PageName)
        """
        var_string = to_csv(page_id_list)
        self._cur.execute("""
            SELECT PageID, PageName
            FROM Pages
            WHERE PageID IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_page_data(self, page_id_list):
        """
        Returns a list of (PageID, PageName, Length)
        """
        var_string = to_csv(page_id_list)
        self._cur.execute("""
            SELECT PageID, PageName, Length
            FROM Pages
            WHERE PageID IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_page_links(self, page_id_list):
        """
        Returns a list of (PageID, TargetPageID, LinkCounter)
        """
        var_string = to_csv(page_id_list)

        self._cur.execute("""
            SELECT T1.PageID, T2.PageID, T1.Counter
            FROM PageLinks T1
            INNER JOIN Pages T2 ON T1.TargetPageID = T2.PageID
            WHERE T1.PageID IN (%s);
        """ % var_string)

        return self._cur.fetchall()

    def get_documents(self, term_id, min_counter=2, limit=200):
        """
        Returns a list of (PageID, TermID)
        Results are limited to the specified value and only terms
        with a Counter larger than min_counter are returned. Returned
        results are sorted in descending order by Counter.
        """
        self._cur.execute("""
            SELECT SQL_NO_CACHE PageID
            FROM TermOccurrences
            WHERE TermID = %s AND Counter > %s
            LIMIT %s
        """ % (term_id, min_counter, limit))
        return self._cur.fetchall()

    def get_term_occurrences(self, page_id_list, term_id_list):
        """
        Returns a list of (PageID, TermID, Counter)
        """
        v1 = to_csv(page_id_list)
        v2 = to_csv(term_id_list)

        self._cur.execute("""
            SELECT SQL_NO_CACHE PageID, TermID, Counter
            FROM TermOccurrences
            WHERE PageID IN (%s) AND TermID IN (%s);
        """ % (v1, v2))
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
        page_index = dict([(b, a) for a, b in enumerate(page_id_list)])
        page_links = self.get_page_links(page_id_list)

        for page_id, target_page_id, counter in page_links:
            if target_page_id in page_index:
                i = page_index[page_id]
                j = page_index[target_page_id]
                link_matrix[i, j] = counter

        return link_matrix

    def word_concepts(self, text):
        term_list = Counter(word_tokenize(text))

        term_ids = dict(self.get_term_ids(term_list.keys()))
        document_frequencies = dict(self.get_document_frequencies(term_ids.values()))

        query_size = len(term_list)
        query_length = sum(term_list.values())
        query_vector = np.zeros(query_size)
        corpus_size = self.get_corpus_size()

        # Dictionary of page vectors organised by page_id
        page_results = {}
        term_index = {}

        # TODO: Perform tfidf term filtering to reduce the number of terms in the query
        # TODO: This can all be reduced to a single call to TermOccurrences (Where TermID IN ())

        # Retrieve all related pages using the Inverted Index lookup
        for i, (term_name, term_id) in enumerate(term_ids.items()):
            df = document_frequencies[term_id]
            query_vector[i] = tfidf(term_list[term_name], df, query_length, corpus_size)

            term_index[term_id] = i

            for (page_id, ) in self.get_documents(term_id, min_counter=4, limit=200):
                if page_id not in page_results:
                    page_results[page_id] = SearchResult(page_id, None, np.zeros(query_size), 0)

        page_data = dict([(a, (b, c)) for a, b, c in self.get_page_data(page_results.keys())])

        # Calculate the TFIDF vector for each page retrieved
        term_occurrences = self.get_term_occurrences(page_results.keys(), term_ids.values())
        for page_id, term_id, tf in term_occurrences:
            vector = page_results[page_id].vector

            index = term_index[term_id]
            df = document_frequencies[term_id]
            length = page_data[page_id][1]

            vector[index] = tfidf(tf, df, length, corpus_size)

        # Order results by Cosine Similarity
        for page_id, search_result in page_results.items():
            search_result.page_name = page_data[page_id][0]
            search_result.weight = np.dot(query_vector, search_result.vector) / (norm(query_vector) * norm(search_result.vector))

        results = page_results.values()
        results.sort(key=lambda x: x.weight, reverse=True)

        return results
