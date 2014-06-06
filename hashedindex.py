class HashedIndex(object):
    """
    InvertedIndex structure in the form of a hash list implemention.
    """

    def __init__(self):
        self._terms = {}

    def __getitem__(self, term):
        return self._terms[term.lower()]

    def __contains__(self, term):
        return term.lower() in self._terms

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

        self._terms[term_l][document] += 1

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
