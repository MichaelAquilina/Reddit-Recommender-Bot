DROP PROCEDURE IF EXISTS SearchPages;

DELIMITER //

CREATE PROCEDURE SearchPages(IN SearchTerm VARCHAR(100))
BEGIN
	SELECT 
		Pages.PageID, 
		Pages.PageName, 
		TermOccurrences.Counter AS "Term Frequency",
		Pages.Length,
		TermOccurrences.Counter / LOG(Pages.Length) AS Weight
	FROM Pages 
	JOIN TermOccurrences ON Pages.PageID = TermOccurrences.PageID 
	JOIN Terms ON Terms.TermID = TermOccurrences.TermID 
	WHERE Terms.TermName = SearchTerm 
	ORDER BY TermOccurrences.Counter DESC;
END//
