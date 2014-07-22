# coding=utf-8

from wiki import _re_link_pattern


def test_link_pattern_test():
    assert _re_link_pattern.findall(u'[[Göta Canal]]') == [u'Göta Canal']
    assert _re_link_pattern.findall('\'\'[[Apple Inc.]]\'\' and [[Iphone 4|That phone]]') == ['Apple Inc.', 'Iphone 4']
    assert _re_link_pattern.findall('[[The 1st, Avengers]]') == ['The 1st, Avengers']
    assert _re_link_pattern.findall('Performing some [[C* Algebra]] in [[Debian!/Ubuntu?]]!') == ['C* Algebra', 'Debian!/Ubuntu?']
    assert _re_link_pattern.findall('[["Loving" - \'it\']] with [[C++#functions|C plus plus]]') == ['"Loving" - \'it\'', 'C++']
    assert _re_link_pattern.findall('[[Queen (band)|Queen]]') == ['Queen (band)']
    assert _re_link_pattern.findall('[[Target page#Target section|display text]]') == ['Target page']
