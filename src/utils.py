import os
import json


def get_search_path():
    search_path = [os.getcwd()]
    if 'PYTHONPATH' in os.environ:
        search_path += os.environ['PYTHONPATH'].split(':')

    if 'PATH' in os.environ:
        search_path += os.environ['PATH'].split(':')

    return search_path


def load_stopwords(path):
    """
    Loads a stopwords file using the given relative path. Searches in the
    current working directory, PYTHONPATH and PATH before giving up.
    """
    stopwords = set()
    for directory in get_search_path():
        abs_path = os.path.join(directory, path)
        if os.path.exists(abs_path):
            with open(abs_path, 'r') as fp:
                while True:
                    line = fp.readline()
                    if line:
                        stopwords.add(line[:-1])
                    else:
                        return stopwords

    raise IOError('Could not find stopwords file: %s' % path)


def load_db_params(filename='db.json'):
    """
    Loads database parameters to perform a connection with from a json formatted
    file (by default 'db.json'. The method will search in the current working directory, the
    directories in the current PYTHONPATH and PATH in that order. If no db.json
    file is found, None will be returned.
    """
    params = None
    for directory in get_search_path():
        if filename in os.listdir(directory):
            # DB-Settings for performing a connection
            with open(os.path.join(directory, filename), 'r') as fp:
                params = json.load(fp)
            break

    return params


def to_csv(target_list, separate=False):
    if separate:
        format_str = u'(\'%s\'),'
        format_non_str = u'(%s),'
    else:
        format_str = u'\'%s\','
        format_non_str = u'%s,'

    var_string = u''
    for item in target_list:
        if type(item) in (str, unicode):
            var_string += format_str % item
        else:
            var_string += format_non_str % item
    return var_string[:-1]


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
