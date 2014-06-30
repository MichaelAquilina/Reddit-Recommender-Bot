import os


# TODO: Cover with tests
def search_files(path):
    for p1 in os.listdir(path):
        abs_path = os.path.join(path, p1)
        if os.path.isdir(abs_path):
            for p2 in search_files(abs_path):
                yield unicode(p2)
        else:
            yield unicode(abs_path)
