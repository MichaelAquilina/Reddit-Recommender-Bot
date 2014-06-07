from __future__ import division

from math import log10


class HashedIndex(object):
    """
    InvertedIndex structure in the form of a hash list implementation.
    """

    def __init__(self):
        self._terms = {}
        self._documents = set()

    def __getitem__(self, term):
        return self._terms[term.lower()]

    def __contains__(self, term):
        return term.lower() in self._terms

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
        term_l = term.lower()
        document_l = document.lower()

        if term_l not in self._terms:
            self._terms[term_l] = {}

        if document_l not in self._terms[term_l]:
            self._terms[term_l][document_l] = 0

        if document_l not in self._documents:
            self._documents.add(document_l)

        self._terms[term_l][document_l] += 1

    def get_term_frequency(self, term, document):
        """
        Returns the frequency of the term specified in the document.
        """
        term_l = term.lower()
        document_l = document.lower()

        if term_l not in self._terms:
            return 0

        if document_l not in self._terms[term_l]:
            return 0

        return self._terms[term_l][document_l]

    def get_document_frequency(self, term):
        """
        Returns the number of documents the specified term appears in.
        """
        term_l = term.lower()

        if term_l not in self._terms:
            return 0
        else:
            return len(self._terms[term_l])

    def terms(self):
        return self._terms.keys()

    def documents(self):
        return self._documents

    def items(self):
        return self._terms

    def get_tfidf(self, term, document):
        """
        Returns the Term-Frequency Inverse-Document-Frequency value for the given
        term in the specified document.
        """
        n = len(self._documents)
        tf = self.get_term_frequency(term, document)

        # Add 1 to document frequency to prevent divide by 0
        df = 1 + self.get_document_frequency(term)

        return tf * log10(n / df)

    def save(self, path, compressed=False):
        import json

        if compressed:
            import bz2
            fp = bz2.BZ2File(path, 'w')
        else:
            fp = open(path, 'w')

        json.dump(self._terms, fp, indent=5)
        fp.close()

    def load(self, path, compressed=False):
        import json
        self._documents = set()

        if compressed:
            import bz2
            fp = bz2.BZ2File(path, mode='r')
        else:
            fp = open(path, 'r')

        self._terms = json.load(fp)
        fp.close()

        # Need to search for the documents
        # Not the most efficient but definitely the simplest
        for item in self._terms.values():
            for document in item.keys():
                self._documents.add(document)
