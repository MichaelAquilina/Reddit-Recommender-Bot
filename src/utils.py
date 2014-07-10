import os


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
