import unittest

from url import *


class UrlTest(unittest.TestCase):

    def setUp(self):
        self.test1 = Url('http://www.Github.com')
        self.test2 = Url('http://www.MyUrl.co.uk/some/Path/Example?A=1&B=2')
        self.test3 = Url('http://My.domain.org/')
        self.test4 = Url('http://some.Page.com.mt/watch?v=somevalue')

    def test_normalize_hostname(self):
        assert self.test1.hostname == 'github.com'
        assert self.test2.hostname == 'myurl.co.uk'
        assert self.test3.hostname == 'my.domain.org'

    def test_normalize_path(self):
        assert self.test1.path == '/'
        assert self.test2.path == '/some/path/example'
        assert self.test3.path == '/'

    def test_normalize_query(self):
        assert self.test1.query == self.test3.query == ''
        assert self.test2.query == 'a=1&b=2'
        assert self.test4.query == 'v=somevalue'

    def test_geturl(self):
        assert self.test1.geturl() == 'http://github.com'
        assert self.test2.geturl() == 'http://myurl.co.uk/some/path/example?a=1&b=2'
        assert self.test3.geturl() == 'http://my.domain.org'
        assert self.test4.geturl() == 'http://some.page.com.mt/watch?v=somevalue'

    def test_normalized_equality(self):
        assert Url('http://www.GitHub.com') == Url('http://github.com/')
        assert Url('http://www.mydomain.org/path') == Url('http://MYDOMAIN.org/PATH/')
        assert not Url('http://www.mydomain.org/?v=20') == Url('http://www.mydomain.org')

    def test_normalized_inequality(self):
        assert Url('http://www.google.com') != Url('http://www.google.co.uk')
        assert Url('http://www.mydomain.org?a=b') != Url('http://www.mydomain.org')
        assert Url('http://sub.domain.org') != Url('http://domain.org')

    def test_normalized_hash(self):
        assert hash(Url('http://www.Google.com?test=1')) == hash(Url('http://google.com/?TEST=1'))
        assert hash(Url('http://my.DOMAIN.org/path/')) == hash(Url('http://MY.domain.org/PATH'))

    def test_normalized_protocol(self):
        assert Url('https://www.google.com') == Url('http://www.google.com')

    def test_normalized_homepage(self):
        assert Url('http://someone.org') == Url('http://www.someone.org/index.html')
