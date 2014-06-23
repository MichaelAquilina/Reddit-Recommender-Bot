from __future__ import division

import unittest
import tempfile

from hashedindex import HashedIndex


def unordered_list_cmp(list1, list2):
    # Check lengths first for slight improvement in performance
    return len(list1) == len(list2) and sorted(list1) == sorted(list2)


class HashedIndexTest(unittest.TestCase):

    def setUp(self):
        self.index = HashedIndex()

        for i in xrange(3):
            self.index.add_term_occurrence('word', 'document1.txt')

        for i in xrange(5):
            self.index.add_term_occurrence('malta', 'document1.txt')

        for i in xrange(4):
            self.index.add_term_occurrence('phone', 'document2.txt')

        for i in xrange(2):
            self.index.add_term_occurrence('word', 'document2.txt')

    def test_case_sensitive_documents(self):
        self.index.add_term_occurrence('word', 'Document2.txt')

        assert self.index.get_term_frequency('word', 'document2.txt') == 2
        assert self.index.get_term_frequency('word', 'Document2.txt') == 1

        assert unordered_list_cmp(self.index.documents(), ['document1.txt', 'document2.txt', 'Document2.txt'])

    def test_getitem(self):
        assert unordered_list_cmp(self.index['word'].keys(), ['document1.txt', 'document2.txt'])
        assert unordered_list_cmp(self.index['malta'].keys(), ['document1.txt'])
        assert unordered_list_cmp(self.index['phone'].keys(), ['document2.txt'])

    def test_getitem_raises_keyerror(self):
        # Trying to get a term that does not exist should raise a key error
        self.assertRaises(KeyError, self.index.__getitem__, 'doesnotexist')

        # Case Insensitive check
        self.assertRaises(KeyError, self.index.__getitem__, 'wORd')

    def test_contains(self):
        assert 'word' in self.index
        assert 'malta' in self.index
        assert 'phone' in self.index

        # Case Insensitive Check
        assert 'WoRd' not in self.index

        # Non-Existent check
        assert 'doesnotexist' not in self.index

    def test_get_total_term_frequency(self):
        assert self.index.get_total_term_frequency('word') == 5
        assert self.index.get_total_term_frequency('malta') == 5
        assert self.index.get_total_term_frequency('doesnotexist') == 0
        assert self.index.get_total_term_frequency('phone') == 4

    def test_get_total_term_frequency_case(self):
        assert self.index.get_total_term_frequency('WORD') == 0
        assert self.index.get_total_term_frequency('Malta') == 0
        assert self.index.get_total_term_frequency('phonE') == 0

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

    def test_get_document_length(self):
        assert self.index.get_document_length('document1.txt') == 8
        assert self.index.get_document_length('document2.txt') == 6

        assert self.index.get_document_length('doesnotexist.txt') == 0

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
        assert unordered_list_cmp(self.index.documents(), ['document1.txt', 'document2.txt'])

        self.index.add_term_occurrence('test', 'document3.txt')
        assert unordered_list_cmp(self.index.documents(), ['document1.txt', 'document2.txt', 'document3.txt'])

        assert 'doesnotexist.txt' not in self.index.documents()

    def test_get_tfidf_relation(self):
        # Test Inverse Document Frequency
        self.assertLess(
            self.index.get_tfidf('word', 'document1.txt'),
            self.index.get_tfidf('malta', 'document1.txt')
        )

    def test_get_tfidf_non_negative(self):
        matrix = self.index.generate_feature_matrix(mode='tfidf')
        assert (matrix >= 0).all()

    def test_get_tfidf_empty_document(self):
        assert self.index.get_tfidf('malta', 'document2.txt') == 0

    def test_get_tfidf_empty_term(self):
        assert self.index.get_tfidf('doesnotexist', 'document1.txt') == 0

    def test_generate_feature_matrix_default(self):
        assert (self.index.generate_feature_matrix() == self.index.generate_feature_matrix(mode='tfidf')).all()

    def test_generate_feature_matrix_tfidf(self):
        features = self.index.terms()
        instances = self.index.documents()

        matrix = self.index.generate_feature_matrix(mode='tfidf')

        assert matrix[instances.index('document1.txt'), features.index('malta')] \
            == self.index.get_tfidf('malta', 'document1.txt')

        assert matrix[instances.index('document2.txt'), features.index('word')] \
            == self.index.get_tfidf('word', 'document2.txt')

        assert matrix[instances.index('document2.txt'), features.index('phone')] \
            == self.index.get_tfidf('phone', 'document2.txt')

        assert matrix[instances.index('document1.txt'), features.index('word')] \
            == self.index.get_tfidf('word', 'document1.txt')

        # Zero Cases
        assert matrix[instances.index('document2.txt'), features.index('malta')] == 0
        assert matrix[instances.index('document1.txt'), features.index('phone')] == 0

    def test_generate_feature_matrix_count(self):
        # Extract the feature and document indices
        features = self.index.terms()
        instances = self.index.documents()

        matrix = self.index.generate_feature_matrix(mode='count')

        # Correct matrix dimensions
        assert matrix.shape == (2, 3)

        # Ensure this method of addressing data works
        assert matrix[instances.index('document1.txt'), features.index('malta')] == 5
        assert matrix[instances.index('document2.txt'), features.index('word')] == 2
        assert matrix[instances.index('document1.txt'), features.index('word')] == 3
        assert matrix[instances.index('document2.txt'), features.index('phone')] == 4

        # Zero cases
        assert matrix[instances.index('document2.txt'), features.index('malta')] == 0
        assert matrix[instances.index('document1.txt'), features.index('phone')] == 0

    def test_generate_feature_matrix_tf(self):
        features = self.index.terms()
        instances = self.index.documents()

        matrix = self.index.generate_feature_matrix(mode='tf')

        assert matrix[instances.index('document1.txt'), features.index('word')] == 3 / 8
        assert matrix[instances.index('document2.txt'), features.index('phone')] == 4 / 6
        assert matrix[instances.index('document1.txt'), features.index('malta')] == 5 / 8

        assert matrix[instances.index('document2.txt'), features.index('malta')] == 0
        assert matrix[instances.index('document2.txt'), features.index('word')] == 2 / 6

    def test_save_load(self):
        # Note mktemp is deprecated but this still works
        path = tempfile.mktemp()
        self.index.save(path)

        index2 = HashedIndex()
        index2.load(path)

        assert self.index == index2

    def test_prune(self):
        self.index = HashedIndex()  # Fresh Index

        for i in xrange(100):
            self.index.add_term_occurrence('word', 'document{}.txt'.format(i))

        for i in xrange(20):
            self.index.add_term_occurrence('text', 'document{}.txt'.format(i))

        self.index.add_term_occurrence('lonely', 'document2.txt')

        self.index.prune(min_frequency=0.1)
        assert 'word' in self.index.terms()
        assert 'text' in self.index.terms()
        assert 'lonely' not in self.index.terms()

        self.index.prune(min_frequency=0.1, max_frequency=0.9)
        assert 'word' not in self.index.terms()
        assert 'text' in self.index.terms()

    def test_save_load_compressed(self):
        path = tempfile.mktemp()
        self.index.save(path, compressed=True)

        index2 = HashedIndex()
        index2.load(path, compressed=True)

        assert self.index == index2

    def test_save_load_meta(self):
        path = tempfile.mktemp()
        self.index.save(path, comment='Testing Comment', custom={'sometest': [1, 2, 3]})

        index2 = HashedIndex()
        meta = index2.load(path)

        assert meta['comment'] == 'Testing Comment'
        assert meta['data-structure'] == str(self.index)
        assert meta['documents'] == len(self.index._documents)
        assert meta['terms'] == len(self.index._terms)
        assert meta['custom'] == {'sometest': [1, 2, 3]}
