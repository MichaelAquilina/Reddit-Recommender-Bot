#! /usr/bin/python

from __future__ import print_function

import MySQLdb
import itertools

# lxml is much much faster than bs4
from lxml import etree

from collections import Counter
from textparser import word_tokenize
from WikiExtractor import clean as clean_wiki_markup

MIN_PAGE_SIZE = 2 * 1024  # 2 KB min size

# Just reading the entire Wikipedia corpus takes 1 hour 15 minutes
# This means that an intermediate format is super important (HashedIndex
# save and load method should suffice in these cases but they might be
# large without appropriate compression)


# Perform a Bulk insert operation for significantly faster performance
def add_term_occurrence(terms, page):
    var_list = Counter(terms)

    # For term occurrence, will probably need to use the Counter class on the terms generator
    # to group items which repeat (which is going to happen often)

    if var_list:
        var_string = u'(%s),' * len(var_list)
        var_string = var_string.rstrip(',')

        cur.execute("""
            INSERT INTO Pages (PageName)
            VALUES (%s);
        """, (page, ))

        pageid = cur.lastrowid

        cur.execute("""
            INSERT IGNORE INTO Terms (TermName)
            VALUES %s;
        """ % var_string, var_list.keys())

        var_string = u'%s,' * len(var_list)
        var_string = var_string.rstrip(',')

        cur.execute("""
            SELECT TermID, TermName FROM Terms
            WHERE TermName IN (%s);
        """ % var_string, var_list.keys())

        term_results = cur.fetchall()
        termids = [(tid, var_list[name]) for (tid, name) in term_results]

        var_string = u'({}, %s, %s),'.format(pageid) * len(term_results)
        var_string = var_string.rstrip(',')

        cur.execute("""
            INSERT INTO TermOccurrences (PageID, TermID, Counter)
            VALUES %s;
        """ % var_string, itertools.chain.from_iterable(termids))


# Definitely possible to prune once term occurrences are implemented
def prune():
    pass

if __name__ == '__main__':
    import bz2
    import time
    import json

    path = '/home/michaela/Development/enwiki-20140502-pages-articles.xml.bz2'

    with open('db.json', 'r') as fp:
        params = json.load(fp)

    connection = MySQLdb.connect(charset='utf8', **params)
    connection.autocommit(False)
    cur = connection.cursor(cursorclass=MySQLdb.cursors.SSCursor)

    cur.execute('DELETE FROM TermOccurrences;')
    cur.execute('DELETE FROM Terms;')
    cur.execute('DELETE FROM Pages;')
    connection.commit()

    t0 = time.time()

    page = False
    page_text = ''
    pages = []
    target = 50000
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
                count += 1
                tree = etree.ElementTree(etree.XML(page_text))
                root = tree.getroot()

                title = root.xpath('title')[0].text
                title = title.replace('\'', '')

                print(count, title, end=' ')

                # Add the text of the page to the index
                text = root.xpath('revision/text')[0].text
                if len(text) > MIN_PAGE_SIZE:
                    clean_text = clean_wiki_markup(text)
                    add_term_occurrence(word_tokenize(clean_text), title)

                    print('(Processed)')
                else:
                    print('(Ignored)')

                page_text = ''
                page = False

                # Commit the changes made in large batches
                if count % 200 == 0:
                    connection.commit()

    connection.commit()

    import pdb
    pdb.set_trace()

    cur.close()
    connection.close()
