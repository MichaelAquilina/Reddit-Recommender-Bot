from __future__ import division

import numpy as np

from math import log10


class HashedIndex(object):
    """
    InvertedIndex structure in the form of a hash list implementation.
    """

    def __init__(self):
        self._terms = {}
        self._documents = set()

    def __getitem__(self, term):
        return self._terms[term]

    def __contains__(self, term):
        return term in self._terms

    def __repr__(self):
        return '<HashedIndex: {} terms, {} documents>'.format(
            len(self._terms), len(self._documents)
        )

    def __eq__(self, other):
        return self.items() == other.items() and self.documents() == other.documents()

    def add_term_occurrence(self, term, document):
        """
        Adds an occurrence of the term in the specified document.
        """
        if term not in self._terms:
            self._terms[term] = {}

        if document not in self._terms[term]:
            self._terms[term][document] = 0

        if document not in self._documents:
            self._documents.add(document)

        self._terms[term][document] += 1

    def get_total_term_frequency(self, term):
        if term not in self._terms:
            return 0

        return sum(self._terms[term].values())

    def get_term_frequency(self, term, document):
        """
        Returns the frequency of the term specified in the document.
        """
        if term not in self._terms:
            return 0

        if document not in self._terms[term]:
            return 0

        return self._terms[term][document]

    def get_document_frequency(self, term):
        """
        Returns the number of documents the specified term appears in.
        """
        if term not in self._terms:
            return 0
        else:
            return len(self._terms[term])

    def terms(self):
        return self._terms.keys()

    def documents(self):
        return list(self._documents)

    def items(self):
        return self._terms

    def get_tfidf(self, term, document):
        """
        Returns the Term-Frequency Inverse-Document-Frequency value for the given
        term in the specified document.
        """
        tf = self.get_term_frequency(term, document)

        # Speeds up performance by avoiding extra calculations
        if tf != 0.0:
            # Add 1 to document frequency to prevent divide by 0
            df = 1 + self.get_document_frequency(term)
            n = 1 + len(self._documents)

            return tf * log10(n / df)
        else:
            return 0.0

    def generate_feature_matrix(self, mode='tfidf'):
        """
        Returns a feature numpy matrix representing the terms and
        documents in this Inverted Index using the tf-idf weighting
        scheme by default. The term counts in each document can
        alternatively be used by specifying scheme='count'

        The size of the matrix is equal to m x n where m is
        the number of documents and n is the number of terms.
        """
        result = np.zeros((len(self._documents), len(self._terms)))

        for i, doc in enumerate(self._documents):
            for j, term in enumerate(self._terms):
                if mode == 'tfidf':
                    result[i, j] = self.get_tfidf(term, doc)
                else:
                    result[i, j] = self.get_term_frequency(term, doc)

        return result

    def prune(self, min_frequency=0.005, max_frequency=1.0):
        n = len(self._documents)

        garbage = []
        for term in self.terms():
            freq = self.get_document_frequency(term) / n

            if freq < min_frequency or freq > max_frequency:
                garbage.append(term)

        for term in garbage:
            del(self._terms[term])

    def save(self, path, compressed=False, **kwargs):
        """
        Saves the state of the HashedIndex as a JSON formatted
        file to the specified path. The optional use of bz2
        compression is also available. Additional meta data can
        be stored through the use of kwargs.
        """
        import json
        import datetime

        if compressed:
            import bz2
            fp = bz2.BZ2File(path, 'w')
        else:
            fp = open(path, 'w')

        meta_data = {
            'data-structure': str(self),
            'date': '{}'.format(datetime.datetime.now()),
            'terms': len(self._terms),
            'documents': len(self._documents),
        }

        # Store custom Kwargs in the meta-data
        for key, value in kwargs.items():
            meta_data[key] = value

        json.dump({
            # Store meta-data for analytical purposes
            'meta': meta_data,
            # Actual HashedIndex data
            'documents': list(self._documents),
            'terms': self._terms,
        }, fp, indent=5)
        fp.close()

    def load(self, path, compressed=False):
        """
        Loads a HashedIndex state from a JSON formatted file that
        was previously saved. If the file was compressed using bz2,
        the compressed flag must be set to True.
        """
        import json

        if compressed:
            import bz2
            fp = bz2.BZ2File(path, mode='r')
        else:
            fp = open(path, 'r')

        data = json.load(fp)
        fp.close()

        self._documents = set(data['documents'])
        self._terms = data['terms']

        return data['meta']
