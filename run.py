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
            password=self.get_db_password(),
            use_chansey_db=self.get_chansey_use_chansey_db(),
            chansey_host=self.get_chansey_db_host(),
            chansey_port=self.get_chansey_db_port(),
            chansey_name=self.get_chansey_db_name(),
            chansey_user=self.get_chansey_db_user(),
            chansey_password=self.get_chansey_db_password()
        )
    
    def run(self) -> None:
        """
        Runs the NestCollector.
        """
        # Get the OSM data
        osm_data = self.overpass.get_osm_data()

        # Get the nests
        nest = Nest(
            osm_data=osm_data,
            area_names=self.overpass.area_names,
            minimum_m2=self.get_minimum_m2()
        )
        nests = nest.get_nests()

        # Save the nests to the database
        self.db.save_nests(nests)

        # Create the stored procedure for counting the spawnpoints in a nest
        self.db.create_spawnpoints_procedure(self.get_minimum_spawnpoints())

        # Calculate the spawnpoints of the nests
        self.db.call_spawnpoints_procedure()

        # Create the stored procedure for filtering overlapping nests
        self.db.create_filtering_procedure(self.get_maximum_overlap())

        # Filter overlapping nests
        self.db.call_filtering_procedure()

        # Count the final active nests
        active_nests = self.db.count_active_nests()
        logging.info(f'Final active nests: {active_nests}')

    def get_minimum_spawnpoints(self) -> int:
        """
        Returns the minimum spawnpoints of a nest.

        Returns:
            int: The minimum spawnpoints of a nest.
        """
        return int(self.config['NESTS']['MINIMUM_SPAWNPOINTS'])

    def get_maximum_overlap(self) -> int:
        """
        Returns the maximum allowed overlap between nests.

        Returns:
            int: The maximum allowed overlap between nests..
        """
        return int(self.config['NESTS']['MAXIMUM_OVERLAP'])

    def get_minimum_m2(self) -> float:
        """
        Returns the minimum m2 of a nest.

        Returns:
            float: The minimum m2 of a nest.
        """
        return float(self.config['NESTS']['MINIMUM_M2'])

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

    def get_chansey_use_chansey_db(self) -> bool:
        """
        Returns if Chansey should be used.

        Returns:
            bool: If Chansey should be used.
        """
        return self.config['CHANSEY']['USE_CHANSEY_DB'].capitalize() == 'True'

    def get_chansey_db_host(self) -> str:
        """
        Returns the IP host of the Chansey db.

        Returns:
            str: The IP host of the Chansey db.
        """
        return self.config['CHANSEY']['HOST']
    
    def get_chansey_db_port(self) -> str:
        """
        Returns the port of the Chansey db.

        Returns:
            str: The port of the Chansey db.
        """
        return self.config['CHANSEY']['PORT']

    def get_chansey_db_name(self) -> str:
        """
        Returns the Chansey database name.

        Returns:
            str: The Chansey database name.
        """
        return self.config['CHANSEY']['NAME']
    
    def get_chansey_db_user(self) -> str:
        """
        Returns the Chansey database username.

        Returns:
            str: The Chansey database username.
        """
        return self.config['CHANSEY']['USER']
    
    def get_chansey_db_password(self) -> str:
        """
        Returns the Chansey database username password.

        Returns:
            str: The Chansey database username password.
        """
        return self.config['CHANSEY']['PASSWORD']


if __name__ == '__main__':
    nest_collector = NestCollector()
    nest_collector.run()
