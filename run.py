"""
Script to run nestcollector.
"""

import configparser
import logging
import os
import sys

from nestcollector.nest import Nest
from nestcollector.database import Database
from nestcollector.overpass import Overpass

CONFIG_PATH = 'config/config.ini'
CONFIG_EXAMPLE_PATH = 'config/config.ini.example'

CONFIG_AREAS_PATH = 'config/areas.json'
CONFIG_AREAS_EXAMPLE_PATH = 'config/areas.json.example'


class NestCollector:
    """
    Class for running the NestCollector.

    Attributes:
        config (configparser.ConfigParser): The config parser.
        overpass (Overpass): The Overpass API instance.
        database (NestDatabase): The database instance.
    """

    def __init__(self) -> None:
        """
        Initializes the NestCollector class.
        """
        # Set the logging level
        logging.basicConfig(level = logging.INFO)

        # Check that the config file exists
        if not os.path.isfile(CONFIG_PATH):
            logging.error(f'Missing {CONFIG_PATH} file, please copy {CONFIG_EXAMPLE_PATH} and fill it with your database settings!')
            sys.exit(1)

        # Check that the config areas file exists
        if not os.path.isfile(CONFIG_AREAS_PATH):
            logging.error(f"Missing {CONFIG_AREAS_PATH} file, please use 'https://fence.mcore-services.be' to create the geofence!")
            logging.error(f'Example areas file: {CONFIG_AREAS_EXAMPLE_PATH}')
            sys.exit(1)

        # Config
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_PATH)

        # Get the Overpass API instance
        self.overpass = Overpass(areas_path=CONFIG_AREAS_PATH)

        # Get the database instance
        self.db = Database(
            host=self.get_db_host(),
            port=self.get_db_port(),
            name=self.get_db_name(),
            user=self.get_db_user(),
            password=self.get_db_password()
        )
    
    def run(self) -> None:
        """
        Runs the NestCollector.
        """
        osm_data = self.overpass.get_osm_data()
        nest = Nest(osm_data)
        nests = nest.get_nests()
        self.db.save_nests(nests)

    def get_db_host(self) -> str:
        """
        Returns the IP host of the db.

        Returns:
            str: The IP host of the db.
        """
        return self.config['DB']['HOST']

    def get_db_port(self) -> str:
        """
        Returns the port of the db.

        Returns:
            str: The port of the db.
        """
        return self.config['DB']['PORT']
    
    def get_db_name(self) -> str:
        """
        Returns the database name.

        Returns:
            str: The database name.
        """
        return self.config['DB']['NAME']
    
    def get_db_user(self) -> str:
        """
        Returns the database username.

        Returns:
            str: The database username.
        """
        return self.config['DB']['USER']
    
    def get_db_password(self) -> str:
        """
        Returns the database username password.

        Returns:
            str: The database username password.
        """
        return self.config['DB']['PASSWORD']


if __name__ == '__main__':
    nest_collector = NestCollector()
    nest_collector.run()
