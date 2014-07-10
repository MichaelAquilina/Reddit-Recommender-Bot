import tempfile

from testutils import generator_unordered_cmp
from utils import *


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
