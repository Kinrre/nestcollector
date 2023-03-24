#!/bin/bash

folder="$(pwd)"

source $folder/config.ini

start=$(date '+%Y%m%d %H:%M:%S')

## Process golbat log to nests db
# checks
if [[ -z $nest_processing_frequency_hours ]] ;then
  echo "set nest_processing_frequency_hours in config and allign with crontab"
  exit
fi

if [[ ! -f $golbat_pm2_log_path/golbat-out.log ]] ;then
  echo "can't find golbat-out.log, golbat_pm2_log_path set in config"
  exit
fi

#open mysql connection
exec 3> >(MYSQL_PWD=$sql_pass mysql -h$db_ip -P$db_port -u$sql_user $golbat_db -NB)

echo ""
echo "Starting nest processing script"

#create form temp table
echo "Creating temp table for forms"
echo "drop temporary table if exists monform; create temporary table monform as(select pokemon_id,min(form) as form from pokemon group by pokemon_id);" >&3

# process
echo "Processing nests"
timestamp=$(grep NESTS $golbat_pm2_log_path/golbat-out.log | tail -1 | awk '{ print $2,$3 }' | head -c15)

while read -r line ;do
  nestid=$(echo $line | awk '{ print $5 }' | sed 's/://g')
  pokemonid=$(echo $line | awk '{ print $8 }')
  quantity=$(echo $line | awk '{ print $10 }')
  hourly=$( bc -l <<< "scale=2; $quantity / $nest_processing_frequency_hours" )
  pct=$(echo $line | awk '{ print $12 }' | sed 's/(//g')

  if [[ ! -z $pokemonid ]] ;then
    echo  "update nests a left join monform b on a.pokemon_id=b.pokemon_id set a.pokemon_id = $pokemonid , a.pokemon_form=b.form, a.pokemon_count= $quantity , a.pokemon_avg = $hourly , a.pokemon_ratio= $pct , a.updated=unix_timestamp() where a.nest_id=$nestid and a.active=1;" >&3
  fi

done < <(grep "$timestamp.*NESTS" $golbat_pm2_log_path/golbat-out.log | grep -v 'Calculating')

# drop temp table
echo "drop temporary table monform;" >&3

# check nests on min spawns/hr
echo "Adjusting nests table on minimum spawns/hr"
if [[ ! -z $nest_min_spawn_hr ]] ;then
# this might create constant switching but need to compensate for i.e. golbat restart or events
  echo "update nests set discarded=NULL where pokemon_avg >= $nest_min_spawn_hr and active=1 and discarded = 'spawnhr_warn';" >&3
# warned => ban
  echo "update nests set discarded='spawnhr_ban', active=0, pokemon_id=NULL, pokemon_form=NULL where pokemon_avg < $nest_min_spawn_hr and active=1 and discarded = 'spawnhr_warn';" >&3
# not warned => strike 1
  echo "update nests set discarded='spawnhr_warn' where pokemon_avg < $nest_min_spawn_hr and active=1 and (discarded <> 'spawnhr_ban' or discarded is NULL);" >&3
fi

#close mysql connection
sleep 10s
exec 3>&-

## reload golbat nests
echo "Reloading golbat nests"
if [[ -z $golbatsecret ]] ;then
  curl http://127.0.0.1:$golbat_api/api/reload-nests
else
  curl -H "X-Golbat-Secret: $golbatsecret" http://127.0.0.1:$golbat_api/api/reload-nests
fi

#procesing time
stop=$(date '+%Y%m%d %H:%M:%S')
diff=$(printf '%02dm:%02ds\n' $(($(($(date -d "$stop" +%s) - $(date -d "$start" +%s)))/60)) $(($(($(date -d "$stop" +%s) - $(date -d "$start" +%s)))%60)))
echo ""
echo "[$start] [$stop] [$diff] Nest processing from Golbat log done"
