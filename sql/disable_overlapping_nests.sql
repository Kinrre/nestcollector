CREATE PROCEDURE nest_filter_overlap()
BEGIN

drop temporary table if exists overlapNest;
create temporary table overlapNest as(
select b.nest_id
from nests a, nests b
where
a.active = 1 and
b.active = 1 and
a.m2 > b.m2 and
ST_Intersects(a.polygon,b.polygon) and
ST_Area(ST_Intersection(a.polygon,b.polygon))/ST_Area(b.polygon)*100 > {maximum_overlap}
);

update nests a, overlapNest b set a.active=0, discarded='overlap' where a.nest_id=b.nest_id;

drop temporary table overlapNest;

END;
