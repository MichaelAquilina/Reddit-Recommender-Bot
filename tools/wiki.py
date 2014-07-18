#! /usr/bin/python

from __future__ import print_function

import time
import MySQLdb
import itertools

# lxml is much much faster than bs4
from lxml import etree

from collections import Counter
from textparser import word_tokenize
from WikiExtractor import clean as clean_wiki_markup

from utils import load_db_params

MIN_PAGE_SIZE = 1 * 1024  # 1 KB min size
MIN_PAGE_LENGTH = 300  # Minimum Page Length in terms

# Just reading the entire Wikipedia corpus takes 1 hour 15 minutes
# This means that an intermediate format is super important (HashedIndex
# save and load method should suffice in these cases but they might be
# large without appropriate compression)

# List of Page titles to ignore when they have the following prefix
IGNORE_LIST = ('Wikipedia:', 'Template:', 'File:', 'Category:', 'Help:', 'Portal:')


def setup():
    cur.execute('DROP TABLE IF EXISTS TermOccurrencesTemp;')
    cur.execute('DROP TABLE IF EXISTS TermOccurrences;')
    cur.execute('DROP TABLE IF EXISTS Pages;')
    cur.execute('DROP TABLE IF EXISTS Terms;')

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Pages (
            PageID INT AUTO_INCREMENT PRIMARY KEY,
            PageName VARCHAR(150) NOT NULL,
            Length INT NOT NULL,
            CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=MYISAM CHARACTER SET=utf8 ROW_FORMAT=FIXED;
    """)

    # Create an index on page name as it is used for many search operations
    cur.execute('CREATE INDEX page_name_index ON Pages (PageName);')

    # Using Unique will automatically use an index for TermName in MySQL
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Terms (
            TermID INT AUTO_INCREMENT PRIMARY KEY,
            TermName VARCHAR(40) NOT NULL UNIQUE,
            CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=MYISAM CHARACTER SET=utf8 ROW_FORMAT=FIXED;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS TermOccurrences (
            TermID INT NOT NULL,
            PageID INT NOT NULL,
            Counter INT DEFAULT 0 NOT NULL,
            FOREIGN KEY (TermID) REFERENCES Terms(TermID) ON DELETE CASCADE,
            FOREIGN KEY (PageID) REFERENCES Pages(PageID) ON DELETE CASCADE,
            PRIMARY KEY (TermID, PageID)
        ) ENGINE=MYISAM CHARACTER SET=utf8 ROW_FORMAT=FIXED;
    """)

    # Complete copy of TermOccurrences structure
    cur.execute("""
        CREATE TABLE IF NOT EXISTS TermOccurrencesTemp (
            TermID INT NOT NULL,
            PageID INT NOT NULL,
            Counter INT DEFAULT 0 NOT NULL,
            PRIMARY KEY (TermID, PageID)
        ) ENGINE=MYISAM CHARACTER SET=utf8 ROW_FORMAT=FIXED;
    """)


def prune():
    prune_start = time.time()

    # Moves Items from the temporary TermOccurrences table to permanent storage
    cur.execute("""
        INSERT INTO TermOccurrences
        SELECT T1.TermID, T1.PageID, T1.Counter
        FROM TermOccurrencesTemp AS T1
        INNER JOIN (
            SELECT TermID
            FROM TermOccurrencesTemp
            GROUP BY TermID
            HAVING SUM(Counter) > 2
        ) AS T2 ON T1.TermID = T2.TermID;
    """)

    # Delete the terms which were not added
    cur.execute("""
        DELETE Terms
        FROM Terms
        LEFT JOIN TermOccurrences ON Terms.TermID = TermOccurrences.TermID
        WHERE PageID IS NULL;
    """)

    print('Pruned %d terms' % cur.rowcount)

    # Clear out the temporary storage
    cur.execute("""
        DELETE FROM TermOccurrencesTemp;
    """)

    print('Pruning took: %d seconds' % (time.time() - prune_start))


# Perform a Bulk insert operation for significantly faster performance
def add_term_occurrence(terms, page):
    var_list = Counter(terms)
    doc_length = sum(var_list.values())

    if doc_length >= MIN_PAGE_LENGTH:
        var_string = u'(%s),' * len(var_list)
        var_string = var_string.rstrip(',')

        cur.execute("""
            INSERT INTO Pages (PageName, Length)
            VALUES (%s, %s);
        """, (page, doc_length))

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

        if term_results:
            termids = [(tid, var_list[name]) for (tid, name) in term_results]

            var_string = u'({}, %s, %s),'.format(pageid) * len(term_results)
            var_string = var_string[:-1]

            cur.execute("""
                INSERT INTO TermOccurrencesTemp (PageID, TermID, Counter)
                VALUES %s;
            """ % var_string, itertools.chain.from_iterable(termids))


def extract_wiki_pages(corpus_path):
    is_page = False
    text_buffer = ''
    text = 'non-empty'

    with bz2.BZ2File(corpus_path, 'r') as fp:
        while text:
            text = fp.readline()

            if '<page>' in text:
                is_page = True

            if is_page:
                text_buffer += text

            if '</page>' in text:
                tree = etree.ElementTree(etree.XML(text_buffer))
                root = tree.getroot()

                title = root.xpath('title')[0].text
                title = title.replace('\'', '')

                # Add the text of the page to the index
                text = root.xpath('revision/text')[0].text

                text_buffer = ''
                is_page = False

                yield title, text


if __name__ == '__main__':
    import bz2
    import argparse

    parser = argparse.ArgumentParser(description='Parse and Index a Wikipedia dump into an SQL database')
    parser.add_argument('path', help='Path to sql data dump compressed in bz2')

    args = parser.parse_args()

    path = args.path

    params = load_db_params()
    if params is None:
        raise ValueError('Could not find db.json')

    connection = MySQLdb.connect(charset='utf8', **params)
    connection.autocommit(False)
    cur = connection.cursor(cursorclass=MySQLdb.cursors.SSCursor)

    setup()
    connection.commit()

    t0 = time.time()

    # Settings dictionary that can be one day stored in a file
    settings = {
        'commit-freq': 200,
        'prune-freq': 2000,
        'speed-freq': 100,
    }

    count = 0
    speed = None
    target = -1

    last_speed_update = time.time()

    for page_title, page_text in extract_wiki_pages(path):
        count += 1

        # If a target is set, break when reached
        if count == target:
            break

        print(count, page_title, end=' ')

        meta = False
        if page_title.endswith('(disambiguation)') or page_title.startswith(IGNORE_LIST):
            meta = True

        if not meta and page_text and len(page_text) > MIN_PAGE_SIZE:
            clean_text = clean_wiki_markup(page_text)
            add_term_occurrence(word_tokenize(clean_text), page_title)

            print('(Processed)', end=' ')
        else:
            print('(Ignored)', end=' ')

        if speed:
            print('(%d pages/sec)' % speed)
        else:
            print('(...)')

        # Prune the database from noisy terms every now and so often
        if count % settings['prune-freq'] == 0:
            prune()

        if count % settings['speed-freq'] == 0:
            # Print Estimated speed every commit
            speed = settings['commit-freq'] / (time.time() - last_speed_update)
            last_speed_update = time.time()

        # Commit the changes made in large batches
        if count % settings['commit-freq'] == 0:
            connection.commit()

    cur.execute('DROP TABLE IF EXISTS TermOccurrencesTemp;')

    connection.commit()

    cur.close()
    connection.close()
