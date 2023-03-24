
#!/bin/bash

folder="$(pwd)"

source $folder/config.ini

## functions
if [[ -z $sql_pass ]] ;then
  query(){
  mysql -u$sql_user -h$db_ip -P$db_port $golbat_db -NB -e "$1;"
  }
else
  query(){
  mysql -u$sql_user -p$sql_pass -h$db_ip -P$db_port $golbat_db -NB -e "$1;"
  }
fi

## execution
mkdir -p tmp

if [[ ! -z $nestcollector_path ]] ;then
  echo ""
  echo "processing nestcollector areas"
  rm -f $folder/tmp/geofences.txt

  query "select distinct(LEFT(fence_data,length(fence_data)-1)) from settings_geofence where geofence_id in (select a.geofence_included from settings_area_mon_mitm a,settings_area b where a.area_id=b.area_id and b.instance_id in ($mad_instances));" | sed 's/\[\"\[/[/g' | sed 's/",/\n/g' | sed 's/"//g' | sed 's/^ //g' > $folder/tmp/geofences.txt
  node $folder/nestcollector_areas.js  $folder/tmp/geofences.txt $nestcollector_path/config/areas.json

  #remove first 2 lines
  sed -i -e 1,2d $nestcollector_path/config/areas.json
  # inset line1 with [
  sed -i '1s/^/[\n/' $nestcollector_path/config/areas.json
  #remove last 2 lines
  for i in $(seq 1 2); do sed -i '$d' $nestcollector_path/config/areas.json; done;
  # insert last line with ]
  sed -i "$ a ]" $nestcollector_path/config/areas.json
  # remove addition []
  sed -s -i -r '/^.{17}$/d' $nestcollector_path/config/areas.json

else
  echo ""
  echo "No nestcollector path set in config"
fi
