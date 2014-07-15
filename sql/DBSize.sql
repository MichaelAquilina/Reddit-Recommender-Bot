DELIMITER //

CREATE PROCEDURE DBSize()
BEGIN
SELECT 
	tables.table_schema AS "Database",
	ROUND(SUM(tables.index_length + tables.data_length)/1024/1024, 1) AS "DB Size in MB"
FROM information_schema.tables
GROUP BY tables.table_schema;
END//