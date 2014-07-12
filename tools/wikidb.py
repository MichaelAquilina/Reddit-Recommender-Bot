from __future__ import print_function

import MySQLdb

# Simple script that creates the necessary tables for the Wikipedia Database Index
if __name__ == '__main__':

    import json
    import os

    if os.path.exists('db.json'):
        with open('db.json', 'r') as fp:
            params = json.load(open('db.json', 'r'))

        connection = MySQLdb.connect(**params)

        # Creates the necessary tables for the database to work
        cur = connection.cursor()

        cur.execute('DROP TABLE IF EXISTS TermOccurrences;')
        cur.execute('DROP TABLE IF EXISTS Pages;')
        cur.execute('DROP TABLE IF EXISTS Terms;')

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Pages (
                PageID INT AUTO_INCREMENT PRIMARY KEY,
                PageName VARCHAR(255) BINARY UNIQUE NOT NULL,
                CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=INNODB;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Terms (
                TermID INT AUTO_INCREMENT PRIMARY KEY,
                TermName VARCHAR(100) UNIQUE,
                CreationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=INNODB;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS TermOccurrences (
                TermID INT NOT NULL,
                PageID INT NOT NULL,
                Counter INT DEFAULT 0,
                FOREIGN KEY (TermID) REFERENCES Terms(TermID),
                FOREIGN KEY (PageID) REFERENCES Pages(PageID),
                PRIMARY KEY (TermID, PageID)
            ) ENGINE=INNODB;
        """)

        cur.close()
        connection.close()

        print('Successfully created the Wikipedia Table Indices')
    else:
        print('Missing db.json configuration file')
