from textparser import word_tokenize


def generator_cmp(gen, list1):
    # Compares a generator to a list for equality
    return list(gen) == list1


def test_word_tokenize():
    assert generator_cmp(word_tokenize('Hello cruel world'), ['Hello', 'cruel', 'world'])
    assert generator_cmp(word_tokenize('New\nLine\rTest'), ['New', 'Line', 'Test'])
    assert generator_cmp(word_tokenize(''), [])

    # Digits
    assert generator_cmp(word_tokenize('gumball800 is cool'), ['gumball800', 'is', 'cool'])
    assert generator_cmp(word_tokenize('90 + ten'), ['90', 'ten'])

    # Remove Case Test
    assert generator_cmp(word_tokenize('Hello WORLD', remove_case=True), ['hello', 'world'])

    # Punctuation Test
    assert generator_cmp(word_tokenize('My! #name **is@ &Michael!'), ['My', 'name', 'is', 'Michael'])

    # Corner cases
    assert generator_cmp(word_tokenize('empty +@@ punctuation'), ['empty', 'punctuation'])
    assert generator_cmp(word_tokenize('This shouldn\'t fail'), ['This', 'shouldnt', 'fail'])
