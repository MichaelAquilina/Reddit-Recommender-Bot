DROP PROCEDURE IF EXISTS ShowPageLinks;

DELIMITER //

CREATE PROCEDURE ShowPageLinks(TargetPage VARCHAR(150))
BEGIN
	SELECT T1.PageID, T1.PageName, T3.PageID "Linked Page ID", T3.PageName AS "Linked Page Name", T2.Counter, T3.Processed
	FROM Pages AS T1
	INNER JOIN PageLinks AS T2 ON T1.PageID = T2.PageID
	INNER JOIN Pages AS T3 ON T2.TargetPageID = T3.PageID
	WHERE T1.PageName = TargetPage
	ORDER BY T2.Counter DESC;
END//