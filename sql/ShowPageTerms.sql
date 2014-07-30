DROP PROCEDURE IF EXISTS ShowPageTerms;

DELIMITER //

CREATE PROCEDURE ShowPageTerms(TargetPage VARCHAR(150))
BEGIN
	SELECT T1.PageID, T2.PageName, T1.TermID, T3.TermName, T1.Counter AS TF
	FROM TermOccurrences T1
	INNER JOIN Pages T2 ON T1.PageID = T2.PageID
	INNER JOIN Terms T3 ON T1.TermID = T3.TermID
	WHERE PageName = TargetPage
	ORDER BY Counter DESC;
END//