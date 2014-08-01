DROP PROCEDURE IF EXISTS ShowPageTerms;

DELIMITER //

CREATE PROCEDURE ShowPageTerms(TargetPage VARCHAR(150))
BEGIN
	SELECT T1.PageID, T2.PageName, T1.TermID, T4.TermName, T1.Counter AS Tf, DocumentFrequency AS Df, T3.Tfidf
	FROM TermOccurrences T1
	INNER JOIN Pages T2 ON T2.PageID = T1.PageID
	INNER JOIN TfidfValues T3 ON T3.PageID = T1.PageID AND T3.TermID = T1.TermID
	INNER JOIN Terms T4 ON T4.TermID = T1.TermID
	INNER JOIN DocumentFrequencies T5 ON T5.TermID = T1.TermID
	WHERE PageName = TargetPage
	ORDER BY Tfidf DESC;
END//