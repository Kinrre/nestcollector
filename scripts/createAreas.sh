
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

  while read -r line ;do
    area=$(echo $line | awk '{print $1}')
    coords=$(echo $line | awk '{$1=""; print $0}')

    echo \[$area\] >> $folder/tmp/geofences.txt
    echo $coords | sed 's/, /xx/g' | sed 's/ /,/g' | sed 's/xx/\n/g' >> $folder/tmp/geofences.txt
    sed -i '$ d' $folder/tmp/geofences.txt
  done < <(query "select fence,coords from $stats_db.geofences where type='mon' or type='both'")

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
