# nestcollector
Collect possible Pokémon Go nests from OSM (Open Street Map) data.

## Getting started

### Prerequisites

* Python3
* MariaDB
* bc
  ```sh
   apt install bc
   ```

## Installation

1. Copy the configuration files and fill it with the corresponding settings.

  ```sh
  cp config/config.ini.example config/config.ini && cp scripts/config.ini.example scripts/config.ini
  ```

2. Create your geofence at https://fence.mcore-services.be or use an existing one and place it in `config/areas.json`.

3. Install the dependencies.
  
  ```sh
  pip3 install -r requirements.txt
  ```

4. Enjoy! 🚀

  ```sh
  python3 run.py
  ```

## Scripts

In order to execute automatically the scripts and keep updated your nests append this line to your crontab:
```sh
05 */6 * * * cd <PATH_TO_NESTCOLLECTOR>/scripts && ./processNests.sh >> <PATH_TO_NESTCOLLECTOR>/crontab.out 2>> <PATH_TO_NESTCOLLECTOR>/crontab.err
```

## Authors
* [Kinrre](https://github.com/Kinrre)
* [dkmur](https://github.com/dkmur)
