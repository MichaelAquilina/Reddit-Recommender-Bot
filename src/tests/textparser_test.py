# ~*~ coding:utf-8 ~*~

from textparser import *


def generator_cmp(gen, list1):
    # Compares a generator to a list for equality
    return list(gen) == list1


def test_null_stemmer():
    stemmer = NullStemmer()
    # No Change should be expected
    assert stemmer.stem('Running, playing with men and dogs') == 'Running, playing with men and dogs'


def test_clean_token():
    assert clean_token('Calvin&amp;Hobbs') == 'Calvin&Hobbs'
    assert clean_token('don\'t') == 'dont'
    assert clean_token('@##hello@#') == 'hello'
    assert clean_token('905!!!') is None


def test_normalize_unicode():
    assert normalize_unicode(u'Klüft skräms inför på fédéral électoral große') == \
        'Kluft skrams infor pa federal electoral groe'

    assert normalize_unicode(u'don’t') == 'dont'


def test_normalize_unicode_str():
    assert normalize_unicode('This is a normal string') == 'This is a normal string'


def test_word_tokenize():
    assert generator_cmp(word_tokenize('Hello cruel world'), ['Hello', 'cruel', 'world'])
    assert generator_cmp(word_tokenize(''), [])
    assert generator_cmp(word_tokenize('empty +@@ punctuation'), ['empty', '+@@', 'punctuation'])
    assert generator_cmp(word_tokenize('This shouldn\'t fail'), ['This', 'shouldn\'t', 'fail'])


def test_word_tokenize_type():
    assert all(type(s) is unicode for s in word_tokenize('Hello World'))


def test_word_tokenize_digits():
    assert generator_cmp(word_tokenize('gumball800 is cool'), ['gumball800', 'is', 'cool'])
    assert generator_cmp(word_tokenize('90 + ten'), ['90', '+', 'ten'])


def test_word_tokenize_remove_case():
    assert generator_cmp(word_tokenize('Hello WORLD', remove_case=True), ['hello', 'world'])


def test_word_tokenize_punctuation():
    assert generator_cmp(word_tokenize('My name is Michael!'), ['My', 'name', 'is', 'Michael!'])


def test_word_tokenize_large_whitespace():
    assert generator_cmp(word_tokenize('This  \n   is \r a   \ttest'), ['This', 'is', 'a', 'test'])


def test_isnumeric_not_words():
    assert not isnumeric('notanumber')
    assert not isnumeric('80eight')


def test_isnumeric_not_time():
    assert not isnumeric('11:45:27')
    assert not isnumeric('15:34')


def test_isnumeric_integer():
    assert isnumeric('8934')
    assert isnumeric('-434')  # Negative Integer


def test_isnumeric_floating_point():
    assert isnumeric('98.34')
    assert isnumeric('-20.345')


def test_isnumeric_scientific_notation():
    assert isnumeric('90e-01')
    assert isnumeric('42E-10')

    assert isnumeric('32e10')
