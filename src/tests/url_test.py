import unittest

from url import *


class UrlTest(unittest.TestCase):

    def setUp(self):
        self.test1 = Url('http://www.Github.com')
        self.test2 = Url('http://www.MyUrl.co.uk/some/Path/Example')
        self.test3 = Url('http://My.domain.org/')

    def test_normalize_hostname(self):
        assert self.test1.hostname == 'github.com'
        assert self.test2.hostname == 'myurl.co.uk'
        assert self.test3.hostname == 'my.domain.org'

    def test_normalize_path(self):
        assert self.test1.path == '/'
        assert self.test2.path == '/some/path/example'
        assert self.test3.path == '/'

    def test_geturl(self):
        assert self.test1.geturl() == 'http://github.com'
        assert self.test2.geturl() == 'http://myurl.co.uk/some/path/example'
        assert self.test3.geturl() == 'http://my.domain.org'

    def test_normalized_equality(self):
        assert Url('http://www.GitHub.com') == Url('http://github.com/')
        assert Url('http://www.mydomain.org/path') == Url('http://MYDOMAIN.org/PATH/')

    def test_normalized_hash(self):
        assert hash(Url('http://www.Google.com')) == hash(Url('http://google.com/'))
        assert hash(Url('http://my.DOMAIN.org/path/')) == hash(Url('http://MY.domain.org/PATH'))
