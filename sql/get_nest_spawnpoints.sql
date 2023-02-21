CREATE PROCEDURE get_nest_spawnpoints()
BEGIN

-- get data
DROP TEMPORARY TABLE IF EXISTS spawnloc;
CREATE TEMPORARY TABLE spawnloc
  (`location` point NOT NULL,
   SPATIAL INDEX(`location`)
  )
  AS (
  SELECT point(lon,lat) as 'location'
  FROM spawnpoint
  WHERE last_seen > unix_timestamp() -604800);

  BEGIN
    DECLARE nest CURSOR FOR SELECT nest_id, polygon FROM nests WHERE polygon IS NOT NULL;
    FOR nest_record IN nest
    DO
      SET @spawns=(select count(*) from spawnloc WHERE ST_CONTAINS(nest_record.polygon, location));
      UPDATE nests SET spawnpoints = @spawns, active = (CASE WHEN @spawns > {minimum_spawnpoints} THEN 1 ELSE 0 END) WHERE nest_id = nest_record.nest_id;
    END FOR;
  END;

DROP TEMPORARY TABLE IF EXISTS spawnloc;

END;
