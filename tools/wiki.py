#! /usr/bin/python

from __future__ import print_function

# lxml is much much faster than bs4
from lxml import etree

from textparser import word_tokenize
from hashedindex import HashedIndex
from WikiExtractor import clean as clean_wiki_markup

MIN_PAGE_SIZE = 1024

# Just reading the entire Wikipedia corpus takes 1 hour 15 minutes
# This means that an intermediate format is super important (HashedIndex
# save and load method should suffice in these cases but they might be
# large without appropriate compression)

if __name__ == '__main__':
    import bz2
    import time

    path = '/home/michaela/Development/enwiki-20140502-pages-articles.xml.bz2'

    t0 = time.time()

    index = HashedIndex()

    page = False
    page_text = ''
    pages = []
    target = 10000
    count = 0

    with bz2.BZ2File(path, 'r') as fp:
        while count < target:
            text = fp.readline()

            if not text:
                break

            if '<page>' in text:
                page = True

            if page:
                page_text += text

            if '</page>' in text:
                if count % 5000 == 0:
                    print('Performing some pruning...')
                    index.prune(min_frequency=0.01)

                count += 1
                tree = etree.ElementTree(etree.XML(page_text))
                root = tree.getroot()

                title = root.xpath('title')[0].text
                print(count, title, end=' ')

                # Add the text of the page to the index
                text = root.xpath('revision/text')[0].text
                if len(text) > MIN_PAGE_SIZE:
                    clean_text = clean_wiki_markup(text)
                    # This is not enough, wiki text contains a lot of markup which should be considered
                    # Need a wiki parser module that handles things like links and special markup
                    # Should probably use he `pre_process` method from main.py
                    for token in word_tokenize(clean_text):
                        if token:
                            index.add_term_occurrence(token, title)

                    print('(Processed)')
                else:
                    print('(Ignored)')

                page_text = ''
                page = False

    print('Total Runtime =', time.time() - t0)

    index.save('/home/michaela/wiki.index.json.bz2', compressed=True)
    import pdb
    pdb.set_trace()
