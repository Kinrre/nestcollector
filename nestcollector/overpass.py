"""
Module containing the Overpass class, which is used to query the OpenStreetMap data.
"""

import logging
import json
import os
import requests
import time

from .timing import human_time

from shapely import geometry
from typing import List


class Overpass:
    """
    Class for querying the OpenStreetMap data using the Overpass API.

    Attributes:
        url (str): The URL of the Overpass API.
        area_names (List[str]): The names of the areas.
        polygons (List[shapely.geometry.Polygon]): The polygons to query.
        bboxes (List[str]): The bounding boxes to query.
    """

    def __init__(self, endpoints: List[str], areas_path: str) -> None:
        """
        Initializes the Overpass class.

        Args:
            areas_path (str): The path to the areas GeoJSON file.
        """
        self.endpoints = endpoints
        self.endpoint_idx = 0
        self.area_names = self._get_names(areas_path)
        self.polygons = self._load_polygons(areas_path)
        self.bboxes = self._get_bboxes()

    def _get_names(self, areas_path: str) -> List[str]:
        """
        Gets the names of the areas from the areas GeoJSON file.

        Args:
            areas_path (str): The path to the areas GeoJSON file.

        Returns:
            List[str]: The names of the areas.
        """
        with open(areas_path, 'r') as f:
            areas = json.load(f)
        return [area['name'] for area in areas]

    def _load_polygons(self, areas_path: str) -> List[geometry.Polygon]:
        """
        Loads the polygon from the areas GeoJSON file.

        Args:
            areas_path (str): The path to the areas GeoJSON file.

        Returns:
            List[shapely.geometry.Polygon]: The polygons to query.
        """
        with open(areas_path, 'r') as f:
            areas = json.load(f)

        polygons = []
        for area in areas:
            coords = []
            for lat, lon in area['path']:
                coords.append((lat, lon))
            polygons.append(geometry.Polygon(coords))
        return polygons

    def _get_bboxes(self) -> List[str]:
        """
        Gets the bounding boxes for the polygons.
        Returns:
            List[str]: The bounding boxes to query.
        """
        bboxes = []
        for polygon in self.polygons:
            minx, miny, maxx, maxy = polygon.bounds
            bboxes.append(f'{minx}, {miny}, {maxx}, {maxy}')
        return bboxes

    def _query_osm_data(self, bbox: str, date: str = '2019-02-24T00:00:00Z') -> dict:
        """
        Queries the OpenStreetMap data for the given date and bounding box.

        Args:
            bbox (str): The bounding box to query.
            date (str, optional): The date to query. Defaults to '2019-02-24T00:00:00Z'.

        Returns:
            dict: The response from the Overpass API.
        """
        query = """
        [out:json]
        [date:"{date}"]
        [timeout:100000]
        [bbox:{bbox}];
        (
            way["landuse"~"farmland|farmyard|grass|greenfield|meadow|orchard|recreation_ground|vineyard"];
            way["leisure"~"garden|golf_course|nature_reserve|park|pitch|playground|recreation_ground"];
            way["natural"~"grassland|heath|moor|plateau|scrub"];

            rel["landuse"~"farmland|farmyard|grass|greenfield|meadow|orchard|recreation_ground|vineyard"];
            rel["leisure"~"garden|golf_course|nature_reserve|park|pitch|playground|recreation_ground"];
            rel["natural"~"grassland|heath|moor|plateau|scrub"];
        );
        out body;
        >;
        out skel qt;
        """
        query = query.format(date=date, bbox=bbox)
        valid_response = False
        osm_data = None
        # Retry if the response is invalid
        while not valid_response:
            response = requests.post(self.endpoints[self.endpoint_idx], data=query)
            if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
                valid_response = True
                osm_data = response.json()
            else:
                logging.warning(f'Invalid response from server: {response.status_code} - {response.headers["Content-Type"]}. Moving to the next endpoint...')
                self.endpoint_idx = (self.endpoint_idx + 1) % len(self.endpoints)
                if self.endpoint_idx % len(self.endpoints) == 0:
                    logging.error('All endpoints are down. Waiting 30 seconds before retrying...')
                    time.sleep(30)
        return osm_data

    def get_osm_data(self, date: str = '2019-02-24T00:00:00Z') -> List[dict]:
        """
        Gets the OpenStreetMap data for the given date and polygon coords and saves it in the data folder.

        Args:
            date (str, optional): The date to query. Defaults to '2019-02-24T00:00:00Z'.

        Returns:
            List[dict]: The OpenStreetMap data.
        """
        # Log the start of the process
        logging.info('Getting OpenStreetMap data...')
        start = time.time()

        # Create the data folder if it doesn't exist
        os.makedirs('data', exist_ok=True)

        # Query the OpenStreetMap data for each polygon coords
        osm_data = []
        for name, coords in zip(self.area_names, self.bboxes):
            # Skip if the data already exists
            if os.path.exists(f'data/{name}.json'):
                logging.info(f'OpenStreetMap data for {name} already exists.')
                with open(f'data/{name}.json', 'r') as f:
                    osm_data.append(json.load(f))
                continue
            
            # Query the OpenStreetMap data
            logging.info(f'Querying OpenStreetMap data for {name} (this will take ages)...')
            _start = time.time()
            _osm_data = self._query_osm_data(coords, date)
            osm_data.append(_osm_data)
            with open(f'data/{name}.json', 'w') as f:
                json.dump(_osm_data, f)
            _end = time.time()
            logging.info(f'Finished querying OpenStreetMap data for {name} in {human_time(_end - _start)}.')
        
        # Log the end of the process
        end = time.time()
        logging.info(f'Finished getting OpenStreetMap data in {human_time(end - start)}.')
        
        return osm_data
