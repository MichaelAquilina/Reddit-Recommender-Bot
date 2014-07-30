DROP TABLE IF EXISTS DocumentFrequencies;

CREATE TABLE DocumentFrequencies (
	TermID INT PRIMARY KEY,
	DocumentFrequency INT NOT NULL,
	FOREIGN KEY (TermID) REFERENCES Terms (TermID)
) ENGINE=MYISAM CHARACTER SET=utf8;

INSERT INTO DocumentFrequencies
SELECT TermID, COUNT(*)
FROM TermOccurrences
GROUP BY TermID;