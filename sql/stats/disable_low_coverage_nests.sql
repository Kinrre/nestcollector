CREATE PROCEDURE nest_filter_low_coverage()
BEGIN

DROP TEMPORARY TABLE IF EXISTS lowCoverage;
CREATE TEMPORARY TABLE lowCoverage AS
    (
        SELECT t.nest_id
        FROM
        (
            SELECT a.nest_id, 100 * SUM(ST_Area(ST_Intersection(a.polygon, b.st_lonlat))) / ST_Area(a.polygon) AS overlap
            FROM nests a, {stats_db}.geofences b
            WHERE a.active = 1 AND (b.type = 'mon' OR b.type = 'both') AND ST_Intersects(a.polygon, b.st_lonlat)
            GROUP BY a.nest_id
        ) t
        WHERE t.overlap < {minimum_coverage}
    );
UPDATE nests a, lowCoverage b SET a.active = 0, discarded = 'low_coverage' WHERE a.nest_id = b.nest_id;
DROP TEMPORARY TABLE lowCoverage;

END;