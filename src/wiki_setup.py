#! /usr/bin/python
from __future__ import print_function

import re
import sys
import time
import MySQLdb
import itertools

# lxml is much much faster than bs4
from lxml import etree

from collections import Counter
from textparser import word_tokenize
from WikiExtractor import clean as clean_wiki_markup

from utils import load_db_params, to_csv, load_stopwords

MIN_PAGE_SIZE = 1 * 1024  # 1 KB min size
MIN_PAGE_LENGTH = 200  # Minimum Page Length in terms

# NOTE ABOUT CORPUS SIZE
# Just reading the entire Wikipedia corpus takes 1 hour 15 minutes

# List of Page titles to ignore when they have the following prefix
IGNORE_LIST = ('List of', 'MediaWiki:', 'Module:', 'Draft:', 'Wikipedia:', 'Template:', 'File:', 'Category:', 'Help:', 'Portal:')

# Wikipedia inner link pattern
# http://en.wikipedia.org/wiki/Wikipedia:Tutorial/Wikipedia_links
_re_link_pattern = re.compile(
    r'\[\[([^]^|^#]+)#?[^]^|]*\|?[^]]*\]\]',
    flags=re.UNICODE
)


# TODO: Write docstring explaining use of tool
# TODO: Generation of TfidfValues, DocumentFrequencies, CorpusSize, TfidfTotals
# TODO: See the following for how to resolve articles that differ by capitalisation
# http://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(capitalization)

def corpus_size_setup():
    cur.execute('DROP TABLE IF EXISTS CorpusSize;')

    cur.execute("""
      CREATE TABLE CorpusSize (
        Size INT NOT NULL
      ) ENGINE=%s CHARACTER SET=utf8;
    """, (engine, ))

    cur.execute("""
        INSERT INTO CorpusSize
        SELECT COUNT(*)
        FROM Pages
        WHERE Processed=1;
    """)


def document_frequencies_setup():
    cur.execute('DROP TABLE IF EXISTS DocumentFrequencies;')

    cur.execute("""
        CREATE TABLE DocumentFrequencies (
          TermID INT PRIMARY KEY,
          DocumentFrequency INT NOT NULL,
          FOREIGN KEY (TermID) REFERENCES Terms(TermID)
        ) ENGINE=%s CHARACTER SET=utf8;
    """, (engine, ))

    cur.execute("""
      INSERT INTO DocumentFrequencies
      SELECT TermID, COUNT(*)
      FROM TermOccurrences
      GROUP BY TermID;
    """)


def tfidf_values_setup():
    cur.execute('DROP TABLE IF EXISTS TfidfValues;')

    cur.execute("""
        CREATE TABLE TfidfValues (
          TermID INT NOT NULL,
          PageID INT NOT NULL,
          Tfidf FLOAT NOT NULL,
          PRIMARY KEY (TermID, PageID),
          FOREIGN KEY (TermID) REFERENCES Terms(TermID),
          FOREIGN KEY (PageID) REFERENCES Pages(PageID)
        ) ENGINE=%s CHARACTER SET=utf8;
    """, (engine, ))

    cur.execute('CREATE INDEX tfidf_index ON TfidfValues(Tfidf);')

    cur.execute("""
      INSERT INTO TfidfValues
      SELECT
        T1.TermID,
        T1.PageID,
        ((1 + LOG(Counter)) / LOG(Length)) * LOG((SELECT Size FROM CorpusSize)/DocumentFrequency)
      FROM TermOccurrences T1
      INNER JOIN DocumentFrequencies T2 ON T1.TermID = T2.TermID
      INNER JOIN Pages T3 ON T1.PageID = T3.PageID;
    """)


def tfidf_totals_setup():
    cur.execute('DROP TABLE IF EXISTS TfidfTotals;')

    cur.execute("""
        CREATE TABLE TfidfTotals (
          PageID INT PRIMARY KEY,
          Total FLOAT NOT NULL
        ) ENGINE=%s CHARACTER SET=utf8;
    """)

    cur.execute('CREATE INDEX tfidf_total_index ON TfidfTotals(Total);')

    cur.execute("""
        INSERT INTO TfidfTotals
        SELECT PageID, SUM(Tfidf)
        FROM TfidfValues
        GROUP BY PageID;
    """)


def post_setup():
    print('Creating fast look up for CorpusSize')
    corpus_size_setup()
    print('Creating fast look up for DocumentFrequencies')
    document_frequencies_setup()
    print('Creating fast look up for TfidfValues')
    tfidf_values_setup()
    print('Creating fast look up for TfidfTotals')
    tfidf_totals_setup()


def setup():
    cur.execute('DROP TABLE IF EXISTS TermOccurrencesTemp;')
    cur.execute('DROP TABLE IF EXISTS TermOccurrences;')
    cur.execute('DROP TABLE IF EXISTS PageLinks;')
    cur.execute('DROP TABLE IF EXISTS Pages;')
    cur.execute('DROP TABLE IF EXISTS Terms;')

    # Using Unique will automatically use an index for PageName in MySQL
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Pages (
            PageID INT AUTO_INCREMENT PRIMARY KEY,
            PageName VARCHAR(250) UNIQUE NOT NULL,
            Length SMALLINT UNSIGNED NOT NULL DEFAULT 0,
            Processed BOOL NOT NULL DEFAULT FALSE,
            CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=%s CHARACTER SET=utf8;
    """, (engine, ))

    # Using Unique will automatically use an index for TermName in MySQL
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Terms (
            TermID INT AUTO_INCREMENT PRIMARY KEY,
            TermName VARCHAR(40) NOT NULL UNIQUE,
            CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=%s CHARACTER SET=utf8;
    """, (engine, ))

    # Table which provides information about links between pages
    cur.execute("""
        CREATE TABLE IF NOT EXISTS PageLinks (
           PageID INT NOT NULL,
           TargetPageID INT NOT NULL,
           Counter SMALLINT UNSIGNED NOT NULL DEFAULT 1,
           FOREIGN KEY (PageID) REFERENCES Pages(PageID) ON DELETE CASCADE,
           FOREIGN KEY (TargetPageID) REFERENCES Pages(PageID) ON DELETE CASCADE,
           PRIMARY KEY (PageID, TargetPageID)
        ) ENGINE=%s ROW_FORMAT=FIXED;
    """, (engine, ))

    cur.execute("""
        CREATE TABLE IF NOT EXISTS TermOccurrences (
            TermID INT NOT NULL,
            PageID INT NOT NULL,
            Counter SMALLINT UNSIGNED DEFAULT 0 NOT NULL,
            FOREIGN KEY (TermID) REFERENCES Terms(TermID) ON DELETE CASCADE,
            FOREIGN KEY (PageID) REFERENCES Pages(PageID) ON DELETE CASCADE,
            PRIMARY KEY (TermID, PageID)
        ) ENGINE=%s ROW_FORMAT=FIXED;
    """, (engine, ))

    cur.execute('CREATE INDEX counter_index ON TermOccurrences (Counter);')

    # Mirrors TermOccurrences structure
    cur.execute("""
        CREATE TABLE IF NOT EXISTS TermOccurrencesTemp (
            TermID INT NOT NULL,
            PageID INT NOT NULL,
            Counter INT DEFAULT 0 NOT NULL,
            CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (TermID, PageID)
        ) ENGINE=%s ROW_FORMAT=FIXED;
    """, (engine, ))


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
    cur.execute('DELETE FROM TermOccurrencesTemp;')

    print('Pruning took: %d seconds' % (time.time() - prune_start))


# Perform a Bulk insert operation for significantly faster performance
def add_page_index(terms, page, intra_links):
    term_list = Counter(terms)
    doc_length = sum(term_list.values())

    if doc_length >= MIN_PAGE_LENGTH:
        cur.execute("""
            SELECT PageID, Processed
            FROM Pages
            WHERE PageName=%s;
        """, (page, ))
        rows = cur.fetchone()
        cur.fetchall()

        if rows:
            page_id, processed = rows
            if processed:
                return  # No decent way to resolve this conflict (Issue #76)
            else:
                cur.execute("""
                    UPDATE Pages
                    SET PageName=%s, Length=%s, Processed=TRUE
                    WHERE PageID=%s;
                """, (page, doc_length, page_id))
        else:
            # On duplicate command is a hack to prevent a select statement
            cur.execute("""
                INSERT IGNORE INTO Pages (PageName, Length, Processed)
                VALUES (%s, %s, TRUE)
            """, (page, doc_length))
            page_id = cur.lastrowid

            # There was a duplicate entry case
            if page_id <= 0:
                return

        filtered_term_list = [a for (a, b) in term_list.items() if b > 1]
        var_string = to_csv(filtered_term_list, separate=True)
        cur.execute("""
            INSERT IGNORE INTO Terms (TermName)
            VALUES %s;
        """ % var_string)

        var_string = to_csv(filtered_term_list, separate=False)
        cur.execute("""
            SELECT TermID, TermName FROM Terms
            WHERE TermName IN (%s);
        """ % var_string)

        term_results = cur.fetchall()

        if term_results:
            termids = [(tid, term_list[name]) for (tid, name) in term_results]

            var_string = u'({},%s,%s),'.format(page_id) * len(term_results)
            var_string = var_string[:-1]

            cur.execute("""
                INSERT INTO TermOccurrencesTemp (PageID, TermID, Counter)
                VALUES %s;
            """ % var_string, itertools.chain.from_iterable(termids))

        var_string = u''
        page_links = {}

        # TODO: Speed this up with join statements
        for link, counter in intra_links.items():
            cur.execute("""
                INSERT INTO Pages (PageName, Processed)
                VALUES (%s, FALSE)
                ON DUPLICATE KEY UPDATE PageID=LAST_INSERT_ID(PageID);
            """, (link, ))

            # Handles conflicts gracefully using a dictionary
            target_page_id = cur.lastrowid
            if target_page_id not in page_links:
                page_links[target_page_id] = 0

            page_links[target_page_id] += counter

        # Generate the link pairs from the built dictionary
        for target_page_id, counter in page_links.items():
            var_string += u'(%d,%d,%d),' % (page_id, target_page_id, counter)

        # Perform one large batch insert rather than individual inserts
        if var_string:
            var_string = var_string[:-1]
            cur.execute("""
                INSERT INTO PageLinks (PageID, TargetPageID, Counter)
                VALUES %s;
            """ % var_string)


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
                content = root.xpath('revision/text')[0].text

                text_buffer = ''
                is_page = False

                yield title, content


if __name__ == '__main__':
    import bz2
    import argparse

    parser = argparse.ArgumentParser(description='Parse and Index a Wikipedia dump into an SQL database')
    parser.add_argument('path', help='Path to sql data dump compressed in bz2')
    parser.add_argument('--post-setup-only', help='Performs a post setup operation', action='store_true')
    parser.add_argument('--cont', help='Continues previous terminated index process', action='store_true')
    parser.add_argument('--force', '-f', help='Forces setting up database without warning prompt', action='store_true')
    parser.add_argument('--engine', choices=('MYISAM', 'INNODB'), default='MYISAM', help='Specify what engine to create tables with')

    args = parser.parse_args()

    path = args.path
    post_flag = args.post_setup_only
    cont_flag = args.cont
    force = args.force
    engine = args.engine

    last_page_id = None
    last_page_title = None

    params = load_db_params()
    if params is None:
        raise ValueError('Could not find db.json')

    connection = MySQLdb.connect(charset='utf8', **params)
    connection.autocommit(False)
    cur = connection.cursor(cursorclass=MySQLdb.cursors.SSCursor)

    if post_flag:
        print('Performing a post setup operation on \'%s\'' % params['db'])
        reply = raw_input('Are you sure you wish to start over \'%s\'? (Y/n): ' % params['db'])
        if reply.lower() not in ('y', 'yes'):
            print('Aborting operation...')
            sys.exit(1)

        post_setup()
        sys.exit(0)

    # Continue or perform fresh start
    if cont_flag:
        print('Continuing previous index operation on \'%s\'' % params['db'])

        cur.execute("""
            SELECT PageID, PageName, CreationDate
            FROM Pages
            WHERE Processed = 1
            ORDER BY CreationDate DESC
            LIMIT 1;
        """)

        last_page_id, last_page_title, creation_date = cur.fetchone()
        cur.fetchall()

        print('Last indexed page was: %s (PageID %d on %s)' % (last_page_title, last_page_id, creation_date))

        # Delete any lingering items which were half way through processing
        cur.execute("""
            DELETE TermOccurrencesTemp
            FROM TermOccurrencesTemp
            WHERE CreationDate >= %s;
        """, (creation_date, ))

        cur.execute("""
            DELETE Terms
            FROM Terms
            WHERE CreationDate >= %s;
        """, (creation_date, ))

        cur.execute("""
            DELETE Pages
            FROM Pages
            WHERE PageID = %s;
        """, (last_page_id, ))

        cur.execute("""
            DELETE PageLinks
            FROM PageLinks
            WHERE PageID = %s
        """, (last_page_id, ))
    else:
        print('Setting up \'%s\' database from scratch using %s' % (params['db'], engine))

        if not force:
            reply = raw_input('Are you sure you wish to delete the database \'%s\' and start over? (Y/n): ' % params['db'])
            if reply.lower() not in ('y', 'yes'):
                print('Aborting operation...')
                sys.exit(1)

        setup()
        connection.commit()

    # Reopen a new cursor to prevent commands out of syncs
    cur.close()
    cur = connection.cursor(cursorclass=MySQLdb.cursors.SSCursor)
    t0 = time.time()

    # Settings dictionary that can be one day stored in a file
    settings = {
        'commit-freq': 200,
        'prune-freq': 4000,
        'speed-freq': 100,
    }

    count = 0
    speed = None
    target = -1

    stopwords = load_stopwords('data/stopwords.txt')

    last_speed_update = time.time()

    for page_title, page_text in extract_wiki_pages(path):
        count += 1

        # If a target is set, break when reached
        if count == target:
            break

        print(count, page_title, end=' ')

        if cont_flag:
            if page_title == last_page_title:
                cont_flag = False
                print('(Found!)', end=' ')
            else:
                print('(Skipping)', end=' ')

        if not cont_flag:
            meta = False
            if page_title.endswith('(disambiguation)') or page_title.startswith(IGNORE_LIST):
                meta = True

            if not meta and page_text and len(page_text) > MIN_PAGE_SIZE:
                try:
                    # Lower and strip required to ensure articles conflate correctly in the Counter object
                    intra_links = Counter(_re_link_pattern.findall(page_text))

                    clean_text = clean_wiki_markup(page_text)
                    add_page_index(word_tokenize(clean_text, remove_urls=True, stopwords=stopwords), page_title, intra_links)
                except MySQLdb.ProgrammingError as e:
                    print('(Sql Error: %s)' % e.message)
                else:
                    print('(Processed)', end=' ')
            else:
                print('(Ignored)', end=' ')

            # Prune the database from noisy terms every now and so often
            if count % settings['prune-freq'] == 0:
                prune()

            # Commit the changes made in large batches
            if count % settings['commit-freq'] == 0:
                connection.commit()

        # Calculate speed regardless of state
        if count % settings['speed-freq'] == 0:
            # Print Estimated speed every commit
            speed = settings['commit-freq'] / (time.time() - last_speed_update)
            last_speed_update = time.time()

        if speed:
            print('(%d pages/sec)' % speed)
        else:
            print('(...)')

    print('Finished reading from the Corpus, cleaning up...')

    post_setup()

    cur.execute('DROP TABLE IF EXISTS TermOccurrencesTemp;')

    connection.commit()

    cur.close()
    connection.close()
