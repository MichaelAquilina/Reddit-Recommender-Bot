from datasource import *

from url import Url


def test_get_url_from_path_empty_dir():
    assert get_url_from_path(
        '', 'reddit.com/r/random%$%'
    ) == 'http://reddit.com/r/random'


def test_get_url_from_path_with_dir():
    assert get_url_from_path(
        '/home/user/pages', '/home/user/pages/example.com/index.html%$%'
    ) == 'http://example.com/index.html'


def test_get_url_from_path_no_symbol():
    assert get_url_from_path(
        '', 'my.domain.com/some/path'
    ) == 'http://my.domain.com/some/path'


def test_get_path_from_url_empty_path():
    # test with empty path urls
    assert get_path_from_url(
        '', Url('http://www.github.com')
    ) == 'github.com/index.html%$%'


def test_get_path_from_url_with_path():
    # Test with paths
    assert get_path_from_url(
        '', Url('http://www.Example.com/some/path/page')
    ) == 'example.com/some/path/page%$%'

    assert get_path_from_url(
        '', Url('http://another.example.co.uk/some/path/page.htm')
    ) == 'another.example.co.uk/some/path/page.htm%$%'


def test_get_path_from_url_root_directory():
    assert get_path_from_url(
        '/root/path', Url('http://my.DOMAIN.com/this/file.html')
    ) == '/root/path/my.domain.com/this/file.html%$%'


def test_get_path_from_url_with_querystring():
    assert get_path_from_url(
        '', Url('http://youtube.com/watch?v=ghsu3u43')
    ) == 'youtube.com/watch?v=ghsu3u43%$%'
