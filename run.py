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
        db (NestDatabase): The database instance.
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
            use_stats_db=self.get_stats_use_stats_db(),
            stats_host=self.get_stats_db_host(),
            stats_port=self.get_stats_db_port(),
            stats_name=self.get_stats_db_name(),
            stats_user=self.get_stats_db_user(),
            stats_password=self.get_stats_db_password()
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
            default_name=self.get_default_name(),
            minimum_m2=self.get_minimum_m2()
        )
        nests = nest.get_nests()

        # Save the nests to the database
        self.db.save_nests(nests)

        # Filter low coverage nests by mon area
        if self.get_stats_use_stats_db():
            self.db.create_low_coverage_procedure(self.get_stats_minimum_coverage())
            self.db.call_low_coverage_procedure()

        # Calculate the spawnpoints of the nests
        self.db.create_spawnpoints_procedure(self.get_minimum_spawnpoints())
        self.db.call_spawnpoints_procedure()

        # Filter overlapping nests
        self.db.create_overlapping_procedure(self.get_maximum_overlap())
        self.db.call_overlappping_procedure()

        # Count the final active nests
        active_nests = self.db.count_active_nests()
        logging.info(f'Final active nests: {active_nests}')

    def get_default_name(self) -> str:
        """
        Returns the default name of a nest.

        Returns:
            str: The default name of a nest.
        """
        return self.config['NESTS']['DEFAULT_NAME']

    def get_minimum_spawnpoints(self) -> int:
        """
        Returns the minimum spawnpoints of a nest.

        Returns:
            int: The minimum spawnpoints of a nest.
        """
        return int(self.config['NESTS']['MINIMUM_SPAWNPOINTS'])

    def get_minimum_m2(self) -> float:
        """
        Returns the minimum m2 of a nest.

        Returns:
            float: The minimum m2 of a nest.
        """
        return float(self.config['NESTS']['MINIMUM_M2'])
    
    def get_maximum_overlap(self) -> int:
        """
        Returns the maximum allowed overlap between nests.

        Returns:
            int: The maximum allowed overlap between nests.
        """
        return int(self.config['NESTS']['MAXIMUM_OVERLAP'])

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

    def get_stats_use_stats_db(self) -> bool:
        """
        Returns if Stats should be used.

        Returns:
            bool: If Stats should be used.
        """
        return self.config['STATS']['USE_STATS_DB'].capitalize() == 'True'
    
    def get_stats_minimum_coverage(self) -> int:
        """
        Returns the minimum coverage of a nest.

        Returns:
            int: The minimum coverage of a nest.
        """
        return int(self.config['STATS']['MINIMUM_COVERAGE'])

    def get_stats_db_host(self) -> str:
        """
        Returns the IP host of the Stats db.

        Returns:
            str: The IP host of the Stats db.
        """
        return self.config['STATS']['HOST']
    
    def get_stats_db_port(self) -> str:
        """
        Returns the port of the Stats db.

        Returns:
            str: The port of the Stats db.
        """
        return self.config['STATS']['PORT']

    def get_stats_db_name(self) -> str:
        """
        Returns the Stats database name.

        Returns:
            str: The Stats database name.
        """
        return self.config['STATS']['NAME']
    
    def get_stats_db_user(self) -> str:
        """
        Returns the Stats database username.

        Returns:
            str: The Stats database username.
        """
        return self.config['STATS']['USER']
    
    def get_stats_db_password(self) -> str:
        """
        Returns the Stats database username password.

        Returns:
            str: The Stats database username password.
        """
        return self.config['STATS']['PASSWORD']


if __name__ == '__main__':
    nest_collector = NestCollector()
    nest_collector.run()
