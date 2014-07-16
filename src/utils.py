import os
import json


def load_db_params():
    params = None
    search_path = [os.getcwd()]
    if 'PYTHONPATH' in os.environ:
        search_path += os.environ['PYTHONPATH'].split(':')

    if 'PATH' in os.environ:
        search_path += os.environ['PATH'].split(':')

    for directory in search_path:
        if 'db.json' in os.listdir(directory):
            # DB-Settings for performing a connection
            with open(os.path.join(directory, 'db.json'), 'r') as fp:
                params = json.load(fp)

    return params


# TODO: Cover with tests
def search_files(path, relative=False):
    for p1 in os.listdir(path):
        abs_path = os.path.join(path, p1)
        if os.path.isdir(abs_path):
            for p2 in search_files(abs_path):
                if relative:
                    yield unicode(os.path.relpath(p2, path))
                else:
                    yield unicode(p2)
        else:
            if relative:
                yield unicode(os.path.relpath(abs_path, path))
            else:
                yield unicode(abs_path)
