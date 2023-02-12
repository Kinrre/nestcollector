# nestcollector
Collect possible Pokémon Go nests from OSM (Open Street Map) data.

## Getting started

### Prerequisites

* Python3

## Installation

1. Copy the configuration file and fill it with the database settings.

  ```sh
  cp config/config.ini.example config/config.ini
  ```

2. Create your geofence at https://fence.mcore-services.be and place it in `config/areas.json`.

3. Install the dependencies.
  
  ```sh
  pip3 install -r requirements.txt
  ```

4. Enjoy!

  ```sh
  python3 run.py
  ```

## Author
* [Kinrre](https://github.com/Kinrre)
