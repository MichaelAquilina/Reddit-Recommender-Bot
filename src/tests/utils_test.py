import os
import tempfile

from testutils import generator_unordered_cmp
from utils import *


def test_get_search_path():
    assert os.getcwd() in get_search_path()
    os.environ['PYTHONPATH'] = '/test/path'
    assert '/test/path' in get_search_path()

    for p in os.environ['PATH'].split(':'):
        assert p in get_search_path()


def test_to_csv():
    assert to_csv(['hello', 'world']) == u'\'hello\',\'world\''
    assert to_csv([1, 2, 3, 4, 100]) == u'1,2,3,4,100'
    assert to_csv([1, 'hello']) == u'1,\'hello\''
    assert to_csv((u'tuple', 123)) == u'\'tuple\',123'


def test_search_files():
    expected_abs = []
    expected_rel = []

    tempdir = tempfile.mkdtemp()
    for i in xrange(10):
        tf = tempfile.mktemp(suffix=str(i), dir=tempdir)
        expected_abs.append(tf)
        expected_rel.append(os.path.relpath(tf, tempdir))
        with open(tf, 'w') as fp:
            fp.write('Temporary data')

    assert generator_unordered_cmp(search_files(tempdir), expected_abs)
    assert generator_unordered_cmp(search_files(tempdir, relative=True), expected_rel)


def test_search_files_recursive():
    expected_abs = []
    expected_rel = []

    tempdir = tempfile.mkdtemp()
    current = tempdir

    for i in xrange(10):
        tf = tempfile.mktemp(suffix=str(i), dir=current)
        expected_abs.append(tf)
        expected_rel.append(os.path.relpath(tf, tempdir))
        with open(tf, 'w') as fp:
            fp.write('Temporary Data')
        current = tempfile.mkdtemp(dir=current)

    assert generator_unordered_cmp(search_files(tempdir), expected_abs)
    assert generator_unordered_cmp(search_files(tempdir, relative=True), expected_rel)
