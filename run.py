"""
Script to run nestcollector.
"""

import logging
import os
import sys

from nestcollector.overpass import Overpass

CONFIG_PATH = 'config/config.ini'
CONFIG_EXAMPLE_PATH = 'config/config.ini.example'

CONFIG_AREAS_PATH = 'config/areas.json'
CONFIG_AREAS_EXAMPLE_PATH = 'config/areas.json.example'


class NestCollector:
    """
    Class for running the NestCollector.

    Attributes:
        overpass (Overpass): The Overpass API instance.
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

        # Get the Overpass API instance
        self.overpass = Overpass(areas_path=CONFIG_AREAS_PATH)
    
    def run(self) -> None:
        """
        Runs the NestCollector.
        """
        self.overpass.get_osm_data()


if __name__ == '__main__':
    nest_collector = NestCollector()
    nest_collector.run()
