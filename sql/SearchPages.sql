DELIMITER //

CREATE PROCEDURE SearchPages(IN SearchTerm VARCHAR(100))
BEGIN
	SELECT 
		Pages.PageID, 
		Pages.PageName, 
		TermOccurrences.Counter AS "Term Frequency"
	FROM Pages 
	JOIN TermOccurrences ON Pages.PageID = TermOccurrences.PageID 
	JOIN Terms ON Terms.TermID = TermOccurrences.TermID 
	WHERE Terms.TermName = SearchTerm 
	ORDER BY TermOccurrences.Counter DESC;
END//