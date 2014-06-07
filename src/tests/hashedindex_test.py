from __future__ import division

import unittest

from hashedindex import HashedIndex


def unordered_list_cmp(list1, list2):
    # Check lengths first for slight improvement in performance
    return len(list1) == len(list2) and sorted(list1) == sorted(list2)


class HashedIndexTest(unittest.TestCase):

    def setUp(self):
        self.index = HashedIndex()

        for i in xrange(3):
            self.index.add_term_occurrence('word', 'document1.txt')

        for i in xrange(3):
            self.index.add_term_occurrence('malta', 'document1.txt')

        # Document names should also be case insensitive
        for i in xrange(2):
            self.index.add_term_occurrence('malta', 'DocumenT1.txt')

        for i in xrange(4):
            self.index.add_term_occurrence('phone', 'document2.txt')

        for i in xrange(2):
            self.index.add_term_occurrence('word', 'document2.txt')

    def test_getitem(self):
        assert unordered_list_cmp(self.index['word'].keys(), ['document1.txt', 'document2.txt'])
        assert unordered_list_cmp(self.index['malta'].keys(), ['document1.txt'])
        assert unordered_list_cmp(self.index['phone'].keys(), ['document2.txt'])

        # Case Insensitive check
        assert self.index['word'] == self.index['WoRD']

        # Trying to get a term that does not exist should raise a key error
        self.assertRaises(KeyError, self.index.__getitem__, 'doesnotexist')

    def test_contains(self):
        assert 'word' in self.index
        assert 'malta' in self.index
        assert 'phone' in self.index

        # Case Insensitive Check
        assert 'WoRd' in self.index

        # Non-Existent check
        assert 'doesnotexist' not in self.index

    def test_get_term_frequency(self):
        # Check Existing cases
        assert self.index.get_term_frequency('word', 'document1.txt') == 3
        assert self.index.get_term_frequency('malta', 'document1.txt') == 5
        assert self.index.get_term_frequency('phone', 'document2.txt') == 4
        assert self.index.get_term_frequency('word', 'document2.txt') == 2

        # Check non existing cases
        assert self.index.get_term_frequency('malta', 'document2.txt') == 0
        assert self.index.get_term_frequency('phone', 'document1.txt') == 0
        assert self.index.get_term_frequency('doesnotexist', 'document1.txt') == 0

    def test_get_document_frequency(self):
        assert self.index.get_document_frequency('word') == 2
        assert self.index.get_document_frequency('malta') == 1
        assert self.index.get_document_frequency('phone') == 1

        assert self.index.get_document_frequency('doesnotexist') == 0

    def test_get_terms(self):
        assert unordered_list_cmp(self.index.terms(), ['word', 'malta', 'phone'])

        self.index.add_term_occurrence('test', 'document3.txt')
        assert unordered_list_cmp(self.index.terms(), ['word', 'malta', 'phone', 'test'])

        assert 'doesnotexist' not in self.index.terms()

    def test_get_items(self):
        assert self.index.items() == {
            'word': {'document1.txt': 3, 'document2.txt': 2},
            'malta': {'document1.txt': 5},
            'phone': {'document2.txt': 4}
        }

    def test_get_documents(self):
        assert self.index.documents() == {'document1.txt', 'document2.txt'}

        self.index.add_term_occurrence('test', 'document3.txt')
        assert self.index.documents() == {'document1.txt', 'document2.txt', 'document3.txt'}

        assert 'doesnotexist.txt' not in self.index.documents()

    def test_get_tfidf(self):
        # Test Inverse Document Frequency
        self.assertLess(
            self.index.get_tfidf('word', 'document1.txt'),
            self.index.get_tfidf('malta', 'document1.txt')
        )

        # No presence in document
        assert self.index.get_tfidf('malta', 'document2.txt') == 0

        # Non-existent term should have no weight
        assert self.index.get_tfidf('doesnotexist', 'document1.txt') == 0
