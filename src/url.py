import urlparse


class Url(object):
    def __init__(self, url_string):
        url_data = urlparse.urlparse(url_string.lower())
        self.hostname = url_data.hostname
        self.path = url_data.path

        # Normalise paths the way performed in browsers
        if self.path == '' or self.path == '/':
            self.path = '/'
        else:
            self.path = self.path.rstrip('/')

        if 'www.' in self.hostname:
            self.hostname = self.hostname.replace('www.', '')

    def geturl(self):
        return 'http://%s%s' % (self.hostname, self.path.rstrip('/'))

    def __eq__(self, other):
        return self.hostname == other.hostname and self.path == other.path

    def __hash__(self):
        return hash(self.hostname) + hash(self.path)

    def __repr__(self):
        return '<Url: %s>' % self.geturl()
