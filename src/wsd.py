# encoding: utf8

from __future__ import print_function, division

from wikiindex import WikiIndex
from utils import load_db_params


def load_stopwords():
    # Populate custom (more comprehensive) list of stopwords
    stopwords_list = set()
    with open('data/stopwords.txt', 'r') as fp:
        while True:
            line = fp.readline()
            if line:
                stopwords_list.add(line.rstrip())
            else:
                return stopwords_list


if __name__ == '__main__':

    import time

    params = load_db_params('wsd.db.json')

    if not params:
        raise ValueError('Could not load database parameters')

    wiki = WikiIndex(**params)

    print(wiki)

    t0 = time.time()

    results, terms, query_vector = wiki.word_concepts("""
        It’s in the room with you now. It’s more subtle than the surveillance state, more transparent than air,
        more pervasive than light. We may not be aware of the dark matter around us (at least without the
        ingestion of strong hallucinogens), but it’s there nevertheless.

        Although we can't see dark matter, we know a bit about how much there is and where it's located.
        Measurement of the cosmic microwave background shows that 80 percent of the total mass of the Universe
        is made of dark matter, but this can’t tell us exactly where that matter is distributed. From
        theoretical considerations, we expect some regions—the cosmic voids—to have little or none of the
        stuff, while the central regions of galaxies have high density. As with so many things involving dark
        matter, though, it’s hard to pin down the details.
    """)

    print(results[:20])

    results, terms, query_vector = wiki.word_concepts(""""
        While Valve and its Steam distribution platform have been pushing Linux as the future of PC gaming for a
        long while now, the folks at online store GOG have contented themselves with PC and Mac software. That
        situation changed today, as GOG (formerly Good Old Games) announced support for Linux, offering over 50
        titles for DRM-free download.
    """)

    print(results[:20])

    results, terms, query_vector = wiki.word_concepts("""
        The original open source software “Benevolent Dictator For Life” and author of Python, Guido van Rossum,
        is leaving Google to join Dropbox, the startup will announce later today. Van Rossum was a software
        engineer at Google since 2005, and should be a huge help as Dropbox is built on Python. He’s the latest
        big hire by the cloud storage startup that’s capitalizing on its 100 million-user milestone.
    """, n=10)

    print(results[:20])

    print('Runtime = {}'.format(time.time() - t0))
