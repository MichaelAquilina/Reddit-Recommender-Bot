import os


# TODO: Cover with tests
def search_files(path):
    for p1 in os.listdir(path):
        abs_path = os.path.join(path, p1)
        if os.path.isdir(abs_path):
            for p2 in search_files(abs_path):
                yield p2
        else:
            yield abs_path


def get_path_from_url(target_dir, url):
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
