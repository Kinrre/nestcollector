CREATE PROCEDURE nest_filter_overlap()
BEGIN

DROP TEMPORARY TABLE IF EXISTS overlapNest;
CREATE TEMPORARY TABLE overlapNest AS
    (
        SELECT b.nest_id
        FROM nests a, nests b
        WHERE a.active = 1 AND b.active = 1 AND a.m2 > b.m2 AND ST_Intersects(a.polygon, b.polygon) AND ST_Area(ST_Intersection(a.polygon,b.polygon)) / ST_Area(b.polygon) * 100 > {maximum_overlap}
    );
UPDATE nests a, overlapNest b SET a.active=0, discarded = 'overlap' WHERE a.nest_id=b.nest_id;
DROP temporary TABLE overlapNest;

END;
