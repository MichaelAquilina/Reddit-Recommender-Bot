DROP TABLE IF EXISTS TfidfVales;

CREATE TABLE TfidfValues (
	TermID INT NOT NULL,
	PageID INT NOT NULL,
	Tfidf FLOAT NOT NULL,
	PRIMARY KEY (TermID, PageID),
	FOREIGN KEY (TermID) REFERENCES Terms (TermID),
	FOREIGN KEY (PageID) REFERENCES Pages (PageID)
) ENGINE=MYISAM CHARACTER SET=utf8;

CREATE INDEX tfidf_index ON TfidfValues (Tfidf);

INSERT INTO TfidfValues
SELECT
	T1.TermID, 
	T1.PageID,
	((1 + LOG(Counter)) / LOG(Length)) * LOG((SELECT Size FROM CorpusSize)/DocumentFrequency)
FROM TermOccurrences T1
INNER JOIN DocumentFrequencies T2 ON T1.TermID = T2.TermID
INNER JOIN Pages T3 ON T1.PageID = T3.PageID;