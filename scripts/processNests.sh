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

if [[ ! -f $golbat_latest_log ]] ;then
  echo "can't find $golbat_latest_log, check if correctly set in config"
  exit
fi

#open mysql connection
exec 3> >(MYSQL_PWD=$sql_pass mysql -h$db_ip -P$db_port -u$sql_user $golbat_db -NB)

echo ""
echo "Starting nest processing script"

#create temp table for current active nests updated at least once
if [[ ! -z $poracle_host ]] ;then
  echo "Add current active nests to (temp) table"
  echo "drop table if exists oldnest;" >&3
  echo "create table oldnest (nest_id bigint(20), pokemon_id int(11)) ENGINE=MEMORY as (select nest_id,pokemon_id from nests where active=1 and pokemon_id is not NULL);" >&3
  sleep 1s
fi

# process
echo "Processing nests"
timestamp=$(grep NESTS $golbat_latest_log | tail -1 | awk '{ print $2,$3 }' | head -c15)

while read -r line ;do
  nestid=$(echo $line | awk '{ print $5 }' | sed 's/://g')
  pokemonid=$(echo $line | awk '{ print $8 }')
  quantity=$(echo $line | awk '{ print $10 }')
  hourly=$( bc -l <<< "scale=2; $quantity / $nest_processing_frequency_hours" )
  pct=$(echo $line | awk '{ print $12 }' | sed 's/(//g')

  if [[ ! -z $pokemonid ]] ;then
    echo  "update nests set pokemon_id = $pokemonid , pokemon_form=NULL, pokemon_count= $quantity , pokemon_avg = $hourly , pokemon_ratio= $pct , updated=unix_timestamp() where nest_id=$nestid and active=1;" >&3
  fi

done < <(grep "$timestamp.*NESTS" $golbat_latest_log | grep -v 'Calculating')

#add some form
echo "Updating nest form"
echo "SET SESSION tx_isolation = 'READ-UNCOMMITTED'; drop temporary table if exists monform; create temporary table monform as(select pokemon_id,min(form) as form from pokemon group by pokemon_id);" >&3
echo "update nests a, monform b set a.pokemon_form=b.form where a.active=1 and a.pokemon_id=b.pokemon_id;" >&3
echo "drop temporary table monform;" >&3
#when form is missing i.e. due to use of Golbat mem only set form=0
echo "update nests set pokemon_form=0 where active=1 and pokemon_form is NULL;" >&3


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

sendporacle(){
  echo "Send $counter changed nests to poracle"
  sed -i '1s/^/[/' $folder/tmp/changednests.json
  sed -i '$s/.$/\]/' $folder/tmp/changednests.json
  sed -i 's/\\\\/\\/g' $folder/tmp/changednests.json
  curl -sSk -X POST http://$poracle_host:$poracle_port -H "Expect:" -H "Accept: application/json" -H "Content-Type: application/json" -d @$folder/tmp/changednests.json
#  time=$(date '+%Y%m%d_%H:%M:%S')
#  mv $folder/tmp/changednests.json $folder/tmp/${time}_changednests.json
#  sleep 1s
  rm $folder/tmp/changednests.json


  counter=0
  echo ""
}

# Send Poracle webhook for changed nests
if [[ ! -z $poracle_host ]] ;then
  mkdir -p $folder/tmp
  rm -f $folder/tmp/changednests.json
  sleep 3s
  counter=0
  while read -r line ; do
    reverse=$(echo $line | awk -F': "' '{print $4}' | sed 's/POLYGON((//g' | sed 's/))"}}//g' | sed 's/,/\n/g' | awk '{ print $2,$1}' | tr '\n' ',' | sed 's/,*$//g' | sed 's/,/],[/g' | sed 's/ /,/g')
    echo $line | sed -e "s/POLYGON((.*))\"/[[[$reverse]]]\", \"type\":0, \"poly_type\":0, \"nest_submitted_by\":null/g" >> $folder/tmp/changednests.json
    counter=$((counter+1))
    # send webhook
    if (( $counter > 49 )) ;then sendporacle ;fi
  done < <(MYSQL_PWD=$sql_pass mysql -h$db_ip -P$db_port -u$sql_user $golbat_db -NB -e "select concat('{\"type\": \"nest\", \"message\": ',json_object('nest_id',a.nest_id,'name',a.name,'form',a.pokemon_form,'lat',a.lat,'lon',a.lon,'pokemon_id',a.pokemon_id,'pokemon_count',a.pokemon_count,'pokemon_avg',a.pokemon_avg,'pokemon_ratio',a.pokemon_ratio, 'current_time', unix_timestamp(), 'reset_time', unix_timestamp(), 'poly_path', astext(polygon)),'},') from nests a, oldnest b where a.active=1 and a.nest_id=b.nest_id and a.pokemon_id<>b.pokemon_id;")
  # send remaining webhook
  if [[ -f $folder/tmp/changednests.json ]] ;then sendporacle ;fi
  # drop temp table
  echo "Drop (temp) old nest table"
  echo "drop table oldnest;" >&3
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
