from textparser import word_tokenize


def test_word_tokenize():
    assert word_tokenize('Hello cruel world') == ['Hello', 'cruel', 'world']
    assert word_tokenize('New\nLine\rTest') == ['New', 'Line', 'Test']
    assert word_tokenize('') == []

    # Digits
    assert word_tokenize('gumball800 is cool') == ['gumball800', 'is', 'cool']
    assert word_tokenize('90 + ten') == ['90', 'ten']

    # Remove Case Test
    assert word_tokenize('Hello WORLD', remove_case=True) == ['hello', 'world']

    # Punctuation Test
    assert word_tokenize('My! #name **is@ &Michael!') == ['My', 'name', 'is', 'Michael']

    # Corner cases
    assert word_tokenize('empty +@@ punctuation') == ['empty', 'punctuation']
    assert word_tokenize('This shouldn\'t fail') == ['This', 'shouldnt', 'fail']
