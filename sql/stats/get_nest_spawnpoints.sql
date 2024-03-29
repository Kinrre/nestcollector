CREATE PROCEDURE get_nest_spawnpoints()
BEGIN
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
-- get data
DROP TEMPORARY TABLE IF EXISTS spawnloc;
CREATE TEMPORARY TABLE spawnloc
  (
    `location` point NOT NULL, SPATIAL INDEX(`location`)
  )
  AS
  (
    SELECT point(a.lon,a.lat) as 'location'
    FROM spawnpoint a, {stats_db}.geofences b
    WHERE a.last_seen > unix_timestamp() -604800 AND (b.type = 'mon' or b.type = 'both') AND ST_CONTAINS(b.st, POINT(a.lat, a.lon))
  );
  BEGIN
    DECLARE nest CURSOR FOR SELECT nest_id, polygon FROM nests WHERE polygon IS NOT NULL;
    FOR nest_record IN nest
    DO
      SET @spawns=(SELECT COUNT(*) from spawnloc WHERE ST_CONTAINS(nest_record.polygon, location));
      UPDATE nests SET spawnpoints = @spawns, active = (CASE WHEN @spawns >= {minimum_spawnpoints} THEN 1 ELSE 0 END), discarded = (CASE WHEN @spawns < {minimum_spawnpoints} THEN 'spawnpoints' ELSE '' END) WHERE nest_id = nest_record.nest_id;
    END FOR;
  END;
DROP TEMPORARY TABLE IF EXISTS spawnloc;

END;
