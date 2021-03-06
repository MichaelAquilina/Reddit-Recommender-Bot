# ~*~ coding:utf-8 ~*~

from textparser import *
from testutils import generator_cmp


def test_null_stemmer():
    stemmer = NullStemmer()
    # No Change should be expected
    assert stemmer.stem('Running, playing with men and dogs') == 'Running, playing with men and dogs'


def test_normalize_unicode():
    assert normalize_unicode(u'Klüft skräms inför på fédéral électoral große') == \
        'Kluft skrams infor pa federal electoral groe'

    assert normalize_unicode(u'don’t') == 'dont'


def test_normalize_unicode_str():
    assert normalize_unicode('This is a normal string') == 'This is a normal string'


def test_word_tokenize():
    assert generator_cmp(word_tokenize('Hello cruel world'), ['hello', 'cruel', 'world'])
    assert generator_cmp(word_tokenize(''), [])
    assert generator_cmp(word_tokenize('empty +@@ punctuation'), ['empty', 'punctuation'])
    assert generator_cmp(word_tokenize('This shouldn\'t fail'), ['shouldnt', 'fail'])
    assert generator_cmp(word_tokenize('Cat and dog'), ['cat', 'dog'])
    assert generator_cmp(word_tokenize('I own a Dell laptop'), ['dell', 'laptop'])  # Regression test


def test_word_tokenize_special_punctuation():
    assert generator_cmp(word_tokenize('self-determination'), ['self', 'determination'])
    assert generator_cmp(word_tokenize('Red/Green'), ['red', 'green'])
    assert generator_cmp(word_tokenize('Red\\Green'), ['red', 'green'])


def test_word_tokenize_stopwords():
    assert generator_cmp(word_tokenize('This is a lot of stopwords'), ['lot', 'stopwords'])

    test_case = 'I should get an empty list'
    assert generator_cmp(word_tokenize(test_case, test_case.split()), [])
    assert generator_cmp(word_tokenize(test_case, []), ['should', 'get', 'an', 'empty', 'list'])


def test_word_tokenize_single_letters():
    # Single letter tokens should be completely ignored
    assert generator_cmp(word_tokenize('a e i o u vowels', []), ['vowels'])
    assert generator_cmp(word_tokenize('!!!@#@##@#I *a Gold', []), ['gold'])
    assert generator_cmp(word_tokenize('aa i', []), ['aa'])


def test_word_tokenize_digits():
    # Pure digits should be ignored but combinations of digits and letters should be included
    assert generator_cmp(word_tokenize('gumball800 is cool'), ['gumball800', 'cool'])
    assert generator_cmp(word_tokenize('90 + ten'), ['ten'])


def test_word_tokenize_punctuation():
    # Punctuation should always be removed from front and back
    assert generator_cmp(word_tokenize('!My name is Michael!'), ['name', 'michael'])


def test_word_tokenize_remove_urls():
    assert generator_cmp(
        word_tokenize('This is a www.google.com hello', remove_urls=True),
        ['hello']

    )
    assert generator_cmp(
        word_tokenize('This is another maps.google.com without', remove_urls=False),
        ['another', 'mapsgooglecom', 'without']
    )


def test_word_tokenize_large_whitespace():
    assert generator_cmp(word_tokenize('This  \n   is \r a   \ttest'), ['test'])


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


def test_is_url():
    assert is_url('https://www.example.com')
    assert is_url('http://www.example.co.uk/about')
    assert is_url('http://www.example.com.mt')


def test_is_url_subdomain():
    assert is_url('http://my.domain.com')
    assert is_url('maps.google.com')


def test_is_url_sans_protocol():
    assert is_url('www.google.com')
    assert is_url('www.google.com/')


def test_is_url_invalid():
    assert not is_url('someone@google.com')
    assert not is_url('hello world')
