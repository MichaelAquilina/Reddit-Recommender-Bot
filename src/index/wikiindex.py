from __future__ import division

import math
import MySQLdb
import numpy as np

from numpy.linalg import norm
from collections import Counter

from utils import to_csv, load_stopwords
from textparser import word_tokenize, tfidf

# TODO: Safer SQL queries when using lists as parameters
# TODO: If a fast lookup table is not available, use the slow technique

stopwords = load_stopwords('data/stopwords.txt')


class SearchResult(object):

    def __init__(self, page_id, page_name, vector, weight):
        self.page_id = page_id
        self.page_name = page_name
        self.vector = vector
        self.weight = weight
        self.incoming = None
        self.outgoing = None

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

        # Determine the level of support in the specified database
        self._cur.execute('SHOW TABLES')
        self._available_tables = set()
        for (table, ) in self._cur.fetchall():
            self._available_tables.add(table)

    def __repr__(self):
        return '<WikiIndex %s@%s>' % (self._db, self._host)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._cur.close()
        self._sscur.close()
        self.connection.close()

    def supports_table(self, table):
        return table in self._available_tables

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
        # Attempting to speed this up with a TargetID IN will
        # not work because there is no Index available on TargetID
        var_string = to_csv(page_id_list)

        self._cur.execute("""
            SELECT PageID, TargetPageID, Counter
            FROM PageLinks
            WHERE PageID IN (%s);
        """ % (var_string, ))

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

    def get_tfidf_values(self, page_id_list, term_id_list):
        """
        Returns a list of (PageID, TermID, Tfidf)
        """
        v1 = to_csv(page_id_list)
        v2 = to_csv(term_id_list)

        self._cur.execute("""
            SELECT PageID, TermID, Tfidf
            FROM TfidfValues
            WHERE PageID IN (%s) AND TermID IN (%s);
        """ % (v1, v2))
        return self._cur.fetchall()

    def get_tfidf_totals(self, page_id_list):
        """
        Returns a list of (PageID, Total)
        """
        var_string = to_csv(page_id_list)

        self._cur.execute("""
            SELECT PageID, Total
            FROM TfidfTotals
            WHERE PageID IN (%s);
        """ % var_string)
        return self._cur.fetchall()

    def get_corpus_size(self):
        """
        Returns the size of the corpus which excludes all unprocessed pages.
        """
        self._cur.execute('SELECT Size FROM CorpusSize;')
        (corpus, ) = self._cur.fetchone()
        self._cur.fetchall()

        return corpus

    def generate_normalised_link_matrix(self, pages, page_id_lists, mode='count'):
        if mode not in ('count', 'single'):
            raise ValueError('Unrecognized mode: %s' % mode)

        size = len(pages)
        link_matrix = np.zeros(shape=(size, size))

        # Build an index of page links
        page_index = dict([(b, a) for a, b in enumerate(pages)])

        for page_ids in page_id_lists:
            if page_ids:
                current_pages = set(page_ids)

                page_links = self.get_page_links(page_ids)
                for page_id, target_page_id, counter in page_links:
                    if target_page_id in page_index and target_page_id not in current_pages:
                        i = page_index[target_page_id]
                        j = page_index[page_id]
                        if mode == 'count':
                            link_matrix[i, j] += counter
                        elif mode == 'single':
                            link_matrix[i, j] = 1

        return link_matrix

    def generate_link_matrix(self, page_id_list, mode='count'):
        """
        Generates a matrix containing the number of links between
        a target page (row) and link from an incoming page (column) in each cell.
        Only pages specified in the page_id_list will be included in the matrix.
        """
        size = len(page_id_list)
        link_matrix = np.zeros(shape=(size, size))

        # Build an index of page links
        page_index = dict([(b, a) for a, b in enumerate(page_id_list)])
        page_links = self.get_page_links(page_id_list)

        for page_id, target_page_id, counter in page_links:
            if target_page_id in page_index:
                i = page_index[target_page_id]
                j = page_index[page_id]
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

    def second_order_ranking(self, results, alpha=0.5):
        """
        Order a set of results rated with cosine similarity using a combination of the
        original similarity score and their linkage score. The influence of the link
        score on the final results can be set by the parameter alpha.
        """
        link_matrix = self.generate_link_matrix([sr.page_id for sr in results], mode='single')
        incoming = link_matrix.sum(axis=1)
        outgoing = link_matrix.sum(axis=0)

        weights = np.asarray([sr.weight for sr in results])

        nonzero = incoming > 0
        authority = np.zeros(incoming.size)
        authority[nonzero] = np.clip(outgoing[nonzero] / incoming[nonzero], 1, 8)

        nonzero = authority > 0
        norm_weights = np.zeros(incoming.size)
        norm_weights[nonzero] = weights[nonzero] / authority[nonzero]

        A = alpha * np.dot(link_matrix, norm_weights)
        A *= weights ** 2
        A += 1.5 * weights

        # Assign newly calculated weights
        for i in xrange(len(results)):
            results[i].weight = A[i]

        results.sort(key=lambda x: x.weight, reverse=True)
        return results

    def word_concepts(self, text, title=None, n=15, min_tfidf=0.5):
        """
        Returns a list of word concepts associated with the text ranked in descending order by
        how similar to the original text the concepts are.
        """
        term_list = Counter(word_tokenize(text, stopwords=stopwords))
        query_norm = math.log(1 + sum(term_list.values()))

        # Nothing that can be done
        if query_norm == 0:
            return None, None, None

        # Boost the score of terms in the articles title
        if title is not None:
            title_tokens = Counter(word_tokenize(title, stopwords=stopwords))
            for term, count in title_tokens.items():
                term_list[term] += 2 * count

        term_names = dict([(b, a) for a, b in self.get_term_ids(term_list)])
        document_frequencies = dict(self.get_document_frequencies(term_names))
        corpus_size = self.get_corpus_size()

        # Generate and filter the query vector
        term_weights = {}
        for term_id in term_names:
            term_name = term_names[term_id]
            if term_id in document_frequencies:
                df = document_frequencies[term_id]
                tf = term_list[term_name]

                # Filter terms to remove low weighted terms
                weight = tfidf(tf, df, corpus_size) / query_norm
                if weight > min_tfidf:
                    term_weights[term_id] = weight

        # Lookup table of term->index
        term_index = dict([(b, a) for a, b in enumerate(term_weights.keys())])

        query_vector = np.asarray(term_weights.values())
        query_vector_norm = norm(query_vector)

        # Determine which are the most representative terms
        top_terms = term_weights.items()
        top_terms.sort(key=lambda x: x[1], reverse=True)

        pages_list_results = []

        # larger value of n means possibly more accuracy but at the cost of speed
        pages = set()
        for term_id, term_weight in top_terms[:n]:
            related_pages = self.get_documents(term_id, min_counter=2, limit=40)
            temp_list = []

            # TODO: Might be more pythonic to join the page_list_results
            for (page_id, ) in related_pages:
                temp_list.append(page_id)
                pages.add(page_id)

            pages_list_results.append(temp_list)

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

        if self.supports_table('TfidfTotals'):
            tfidf_totals = dict(self.get_tfidf_totals(pages))
        else:
            tfidf_totals = None

        results = []
        for page_id, page_name, page_length in page_data:
            page_vector = page_vectors[page_id]

            if self.supports_table('TfidfTotals'):
                page_vector /= math.log(tfidf_totals[page_id])
            else:
                page_vector /= math.log(page_length)

            similarity = np.dot(page_vector, query_vector) / (norm(page_vector) * query_vector_norm)
            results.append(SearchResult(page_id, page_name, page_vector, similarity))

        results.sort(key=lambda x: x.weight, reverse=True)

        term_sequence = sorted(term_index.items(), key=lambda x: x[1])

        if results:
            # Second order ranking stuff
            link_matrix = self.generate_normalised_link_matrix([sr.page_id for sr in results], pages_list_results, mode='single')
            incoming = link_matrix.sum(axis=1)
            outgoing = link_matrix.sum(axis=0)

            weights = np.asarray([sr.weight for sr in results])

            nonzero = incoming > 0
            authority = np.zeros(incoming.size)
            authority[nonzero] = np.clip(outgoing[nonzero] / incoming[nonzero], 1, 8)

            nonzero = authority > 0
            norm_weights = np.zeros(incoming.size)
            norm_weights[nonzero] = weights[nonzero] / authority[nonzero]

            alpha = 0.5
            A = alpha * np.dot(link_matrix, norm_weights)
            A *= weights ** 2
            A += 1.5 * weights

            # Assign newly calculated weights
            for i in xrange(len(results)):
                results[i].weight = A[i]
                results[i].incoming = incoming[i]
                results[i].outgoing = outgoing[i]

            # Link matrix wont be returned in the right order because of resorting!!!!
            results.sort(key=lambda x: x.weight, reverse=True)

        return results, [term_names[tid] for tid, index in term_sequence], query_vector
