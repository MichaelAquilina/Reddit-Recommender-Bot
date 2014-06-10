# ~*~ coding:utf-8 ~*~

from textparser import *


def generator_cmp(gen, list1):
    # Compares a generator to a list for equality
    return list(gen) == list1


def test_normalize_unicode():
    assert normalize_unicode(u'Klüft skräms inför på fédéral électoral große') == \
        'Kluft skrams infor pa federal electoral groe'

    assert normalize_unicode(u'don’t') == 'dont'


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


def test_isnumeric():
    assert not isnumeric('notanumber')
    assert not isnumeric('80eight')

    assert isnumeric('8934')  # Integer
    assert isnumeric('-434')  # Negative Integer
    assert isnumeric('98.34')  # Floating point
    assert isnumeric('90e-01')  # Scientific Notation
