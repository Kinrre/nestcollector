"""
Script to run nestcollector.
"""

import logging
import os
import sys

from nestcollector.overpass import Overpass

CONFIG_PATH = 'config/areas.json'
CONFIG_EXAMPLE_PATH = 'config/areas.json.example'


class NestCollector:
    """
    Class for running the NestCollector.

    Attributes:
        config_path (str): The path to the config file.
        config_example_path (str): The path to the example config file.
        overpass (Overpass): The Overpass API instance.
    """

    def __init__(self) -> None:
        """
        Initializes the NestCollector class.
        """
        self.config_path = CONFIG_PATH
        self.config_example_path = CONFIG_EXAMPLE_PATH

        # Set the logging level
        logging.basicConfig(level = logging.INFO)

        # Check that the config file exists
        if not os.path.isfile(CONFIG_PATH):
            logging.error(f'Missing {CONFIG_PATH} file, please use https://fence.mcore-services.be/ to create the geofence!')
            logging.error(f'Example config file: {CONFIG_EXAMPLE_PATH}')
            sys.exit(1)

        # Get the Overpass API instance
        self.overpass = Overpass(areas_path=self.config_path)
    
    def run(self) -> None:
        """
        Runs the NestCollector.
        """
        self.overpass.get_osm_data()


if __name__ == '__main__':
    nest_collector = NestCollector()
    nest_collector.run()
