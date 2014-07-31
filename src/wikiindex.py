from __future__ import division

import math
import MySQLdb
import numpy as np

from numpy.linalg import norm
from collections import Counter

from utils import to_csv, load_stopwords
from textparser import word_tokenize, tfidf

# TODO: Safer SQL queries when using lists as parameters

stopwords = load_stopwords('data/stopwords.txt')


class SearchResult(object):

    def __init__(self, page_id, page_name, vector, weight):
        self.page_id = page_id
        self.page_name = page_name
        self.vector = vector
        self.weight = weight
        self.links_from = None
        self.links_to = None

    def __repr__(self):
        return '%s (%d): %f' % (self.page_name, self.page_id, self.weight)


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
            SELECT TermID, DocumentFrequency
            FROM DocumentFrequencies
            WHERE TermID IN (%s)
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
        Returns a list of (PageID)
        Results are limited to the specified value and only terms
        with a Counter larger than min_counter are returned. Returned
        results are sorted in descending order by Counter.
        """
        self._cur.execute("""
            SELECT PageID
            FROM TermOccurrences
            WHERE TermID = %s AND Counter > %s
            ORDER BY Counter DESC
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
            SELECT PageID, TermID, Counter
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

    def generate_link_matrix(self, page_id_list, mode='count'):
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
                if mode == 'count':
                    link_matrix[i, j] = counter
                elif mode == 'log':
                    link_matrix[i, j] = math.log(counter) + 1 if counter else 0
                elif mode == 'single':
                    link_matrix[i, j] = 1

        return link_matrix

    def visit_article(self, page_id):
        """
        Opens a browser to view the specified article on en.Wikipedia.org
        """
        import urllib
        import webbrowser
        (_, page_name) = self.get_page_names((page_id, ))[0]
        page_name = page_name.replace(' ', '_')
        webbrowser.open('http://en.wikipedia.org/wiki/%s' % urllib.quote(page_name))

    def second_order_ranking(self, results, alpha=0.4):
        """
        Order a set of results rated with cosine similarity using a combination of the
        original similarity score and their linkage score.
        """
        link_matrix = self.generate_link_matrix([sr.page_id for sr in results], mode='single')
        links_from = link_matrix.sum(axis=0)
        links_to = link_matrix.sum(axis=1)

        new_weights = np.zeros(len(results))

        for j in xrange(link_matrix.shape[0]):

            # Items which have no links should not receive a score
            if links_from[j] > 0:
                for i in xrange(link_matrix.shape[1]):
                    if link_matrix[i, j] > 0 and links_from[i] > 0:
                        new_weights[j] += (alpha * link_matrix[i, j] * results[i].weight) / (links_to[i] / links_from[i])

                new_weights[j] *= math.pow(results[j].weight, 2)
                new_weights[j] += 2 * results[j].weight

            results[j].links_from = links_from[j]
            results[j].links_to = links_to[j]

        # Assign newly calculated weights
        for i in xrange(len(results)):
            results[i].weight = new_weights[i]

        results.sort(key=lambda x: x.weight, reverse=True)
        return results

    def word_concepts(self, text, n=15):
        """
        Returns a list of word concepts associated with the text ranked in descending order by
        how similar to the original text the concepts are.
        """
        term_list = Counter(word_tokenize(text, stopwords=stopwords))
        query_norm = math.log(sum(term_list.values()))

        term_names = dict([(b, a) for a, b in self.get_term_ids(term_list)])
        document_frequencies = dict(self.get_document_frequencies(term_names))
        corpus_size = self.get_corpus_size()

        # Generate and filter the query vector
        term_weights = {}
        for term_id in term_names:
            term_name = term_names[term_id]
            df = document_frequencies[term_id]
            tf = term_list[term_name]

            # Filter terms to remove low weighted terms
            weight = tfidf(tf, df, corpus_size) / query_norm
            if weight > 0.5:
                term_weights[term_id] = weight

        # Lookup table of term->index
        term_index = dict([(b, a) for a, b in enumerate(term_weights.keys())])

        query_vector = np.asarray(term_weights.values())
        query_vector_norm = norm(query_vector)

        # Determine which are the most representative terms
        top_terms = term_weights.items()
        top_terms.sort(key=lambda x: x[1], reverse=True)

        # larger value of n means possibly more accuracy but at the cost of speed
        pages = set()
        for term_id, term_weight in top_terms[:n]:
            for (page_id, ) in self.get_documents(term_id, min_counter=2, limit=50):
                pages.add(page_id)

        term_occurrences = self.get_term_occurrences(pages, term_index.keys())
        page_data = self.get_page_data(pages)

        page_vectors = {}
        for page_id, term_id, tf in term_occurrences:
            df = document_frequencies[term_id]
            index = term_index[term_id]
            weight = tfidf(tf, df, corpus_size)

            if page_id not in page_vectors:
                page_vectors[page_id] = np.zeros(query_vector.size)

            page_vectors[page_id][index] = weight

        results = []
        for page_id, page_name, page_length in page_data:
            page_vector = page_vectors[page_id]
            page_vector /= math.log(page_length)

            similarity = np.dot(page_vector, query_vector) / (norm(page_vector) * query_vector_norm)
            results.append(SearchResult(page_id, page_name, page_vector, similarity))

        results.sort(key=lambda x: x.weight, reverse=True)

        term_sequence = sorted(term_index.items(), key=lambda x: x[1])
        return results, [term_names[tid] for tid, index in term_sequence], query_vector
