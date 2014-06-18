import urlparse


class Url(object):
    def __init__(self, url_string):
        url_data = urlparse.urlparse(url_string.lower())
        self.hostname = url_data.hostname
        self.path = url_data.path
        self.query = url_data.query

        # Normalise paths the way performed in browsers
        if self.path == '' or self.path == '/':
            self.path = '/'
        else:
            self.path = self.path.rstrip('/')

        if 'www.' in self.hostname:
            self.hostname = self.hostname.replace('www.', '')

    def geturl(self):
        url_string = 'http://%s%s' % (self.hostname, self.path.rstrip('/'))
        if self.query:
            url_string += '?%s' % self.query

        return url_string

    def __eq__(self, other):
        return self.hostname == other.hostname \
            and self.path == other.path \
            and self.query == other.query

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.hostname) + hash(self.path)

    def __repr__(self):
        return '<Url: %s>' % self.geturl()
