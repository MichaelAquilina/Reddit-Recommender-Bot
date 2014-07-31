# encoding: utf8

from __future__ import print_function, division

import math
import numpy as np

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


def dump_results(path, results, terms, query_vector):

    test = wiki.second_order_ranking(results)
    print(test)

    from numpy.linalg import norm

    with open(path, 'w') as fp:
        fp.write('===Query Vector=== (weight=1.0, norm=%f, distance=0)\n' % norm(query_vector))
        for term, weight in zip(terms, query_vector):
            fp.write('%s: %f, ' % (term, weight))
        fp.write('\n\n')

        for index, (sr) in enumerate(test):
            distance = math.sqrt(np.sum((query_vector - sr.vector) ** 2))
            fp.write(
                '===%s=== (weight=%f, norm=%f, distance=%f, page_id=%d, from=%s, to=%s)\n' % (
                    sr.page_name, sr.weight,
                    norm(sr.vector), distance, sr.page_id,
                    sr.links_from, sr.links_to
                )
            )
            for term, weight in zip(terms, sr.vector):
                fp.write('%s: %f, ' % (term, weight))
            fp.write('\n\n')


if __name__ == '__main__':

    import time
    import os

    params = load_db_params('wsd.db.json')

    if not params:
        raise ValueError('Could not load database parameters')

    wiki = WikiIndex(**params)

    print(wiki)

    target_dir = '/home/michaela/Development'

    t0 = time.time()

    results, terms, query_vector = wiki.word_concepts("""
        Israel attacked a UN-run school housing refugees in Gaza despite warnings that civilians were there,
        the UN has said.

        UN spokesman Chris Gunness said "the world stands disgraced" by the attack, in which 15 died and dozens were
        hurt.

        Israel said an initial inquiry suggested soldiers responded to mortar fire. It called a partial, four-hour
        humanitarian ceasefire but Hamas, which controls Gaza, said it was meaningless.

        More than 1,300 Palestinians and 55 Israelis have died in the conflict.

        Most of the Palestinian deaths have been civilians.
    """)

    print(results[:10])
    dump_results(os.path.join(target_dir, 'gaza.vector'), results, terms, query_vector)

    results, terms, query_vector = wiki.word_concepts("""
        The warming of the planet is driving ocean levels upward through two processes: the melting of land-based ice
        and the thermal expansion of the water in the oceans. Due to the vast energies involved, both of these
        processes are slow, so the ocean levels have only been creeping up a few millimeters a year. That slow pace
        makes it difficult for anyone to perceive the changes.

        But it's clear that those changes are taking place. In the latest indication, the National Oceanic and
        Atmospheric Administration (NOAA) has compiled data on what it calls "nuisance floods," cases where coastal
        communities have to deal with flooding as a result of high tides or minor storms. Over the last 50 years,
        instances of these floods along the East Coast have gone up by anywhere from 300 to 900 percent.
    """)

    print(results[:10])
    dump_results(os.path.join(target_dir, 'globalwarning.vector'), results, terms, query_vector)

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

    print(results[:10])
    dump_results(os.path.join(target_dir, 'darkmatter.vector'), results, terms, query_vector)

    results, terms, query_vector = wiki.word_concepts(""""
        While Valve and its Steam distribution platform have been pushing Linux as the future of PC gaming for a
        long while now, the folks at online store GOG have contented themselves with PC and Mac software. That
        situation changed today, as GOG (formerly Good Old Games) announced support for Linux, offering over 50
        titles for DRM-free download.

        GOG's list of available Linux titles is unsurprisingly dominated by indie titles and overlaps somewhat with
        the more robust list of nearly 600 Linux titles on Steam. But GOG is promoting nearly two dozen titles that
        are being offered on Linux for the first time through GOG, after the site says it "personally ushered [them]
        one by one into the welcoming embrace of Linux gamers" with "special builds prepared by our team." That list
        of new-to-Linux titles on GOG includes some well-remembered, big-name classics like FlatOut (and FlatOut 2),
        Rise of the Triad, Sid Meier's Pirates, and Sid Meier's Colonization (not to mention Duke Nukem 3D, which was
        previously available on Linux).
    """)

    print(results[:10])
    dump_results(os.path.join(target_dir, 'gog.vector'), results, terms, query_vector)

    results, terms, query_vector = wiki.word_concepts("""
        The original open source software “Benevolent Dictator For Life” and author of Python, Guido van Rossum,
        is leaving Google to join Dropbox, the startup will announce later today. Van Rossum was a software
        engineer at Google since 2005, and should be a huge help as Dropbox is built on Python. He’s the latest
        big hire by the cloud storage startup that’s capitalizing on its 100 million-user milestone.
    """)

    print(results[:10])
    dump_results(os.path.join(target_dir, 'guido.vector'), results, terms, query_vector)

    results, terms, query_vector = wiki.word_concepts("""
        The two companies already collaborated to produce Secusmart-equipped BlackBerry phones for German government
        agencies and leadership, including Chancellor Angela Merkel—who had previously been the target of
        NSA eavesdropping.
    """)

    print(results[:10])
    dump_results(os.path.join(target_dir, 'blackberry.vector'), results, terms, query_vector)

    results, terms, query_vector = wiki.word_concepts("""
        Google I/O is a developer conference held each year with two days of deep technical content featuring technical
        sessions and hundreds of demonstrations from developers showcasing their technologies.

        This project is the Android app for the conference. The app supports devices running Android 4.0+, and is
        optimized for phones and tablets of all shapes and sizes. It also contains an Android Wear integration.

        Android L Developer Preview

        We have updated the I/O app with material design and the Android L Developer Preview! For a quick preview of the
        new tactile surfaces, animated touch feedback, bold use of color, and refreshed iconography by checking out this
        teaser video or download the preview APK below.

        Download the I/O app APK for Android L Preview

        To run this APK, you will need a device/emulator set up with the Android L Preview system image. For more
        information, please refer to the Android L Developer Preview page.
    """)

    print(results[:10])
    dump_results(os.path.join(target_dir, 'googleio.vector'), results, terms, query_vector)

    print('Runtime = {}'.format(time.time() - t0))

    wiki.close()
