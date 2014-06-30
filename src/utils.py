import os

from url import Url


# TODO: Cover with tests
def search_files(path):
    for p1 in os.listdir(path):
        abs_path = os.path.join(path, p1)
        if os.path.isdir(abs_path):
            for p2 in search_files(abs_path):
                yield unicode(p2)
        else:
            yield unicode(abs_path)


def get_url_from_path(target_dir, abs_path):
    rel_path = os.path.relpath(abs_path, target_dir)

    if rel_path.endswith('%$%'):
        rel_path = rel_path[:-3]  # Remove special tag character

    return 'http://' + rel_path


def get_path_from_url(target_dir, url):
    if type(url) != Url:
        url = Url(url)

    directory = os.path.join(target_dir, url.hostname)

    # Create subdirs according to the url path
    url_path = url.path.strip('/')

    path_index = url_path.rfind('/')
    if path_index != -1:
        sub_path = url_path[:path_index].lstrip('/')
        directory = os.path.join(directory, sub_path)

        filename = url_path[path_index:].strip('/')
    else:
        filename = url_path

    # Root page directories are "index.html"
    if filename == '':
        filename = 'index.html'

    # Query can uniquely identify a file
    if url.query:
        filename += '?' + url.query

    # Append special character to prevent conflicts with directories
    filename += '%$%'

    return directory, filename
