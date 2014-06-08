from textparser import word_tokenize


def generator_cmp(gen, list1):
    # Compares a generator to a list for equality
    return list(gen) == list1


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
