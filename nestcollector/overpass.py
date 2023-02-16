"""
Module containing the Overpass class, which is used to query the OpenStreetMap data.
"""

from shapely import geometry
from typing import List

import logging
import json
import os
import requests
import time


class Overpass:
    """
    Class for querying the OpenStreetMap data using the Overpass API.

    Attributes:
        url (str): The URL of the Overpass API.
        names (List[str]): The names of the areas.
        polygons (List[shapely.geometry.Polygon]): The polygons to query.
        bboxes (List[str]): The bounding boxes to query.
    """

    def __init__(self, areas_path: str) -> None:
        """
        Initializes the Overpass class.

        Args:
            areas_path (str): The path to the areas GeoJSON file.
        """
        self.url = 'https://overpass.kumi.systems/api/interpreter'
        self.names = self._get_names(areas_path)
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
            way[leisure=park];
            way[landuse=recreation_ground];
            way[leisure=recreation_ground];
            way[leisure=pitch];
            way[leisure=garden];
            way[leisure=golf_course];
            way[leisure=playground];
            way[landuse=meadow];
            way[landuse=grass];
            way[landuse=greenfield];
            way[natural=scrub];
            way[natural=heath];
            way[natural=grassland];
            way[landuse=farmyard];
            way[landuse=vineyard];
            way[landuse=farmland];
            way[landuse=orchard];
            way[natural=plateau];
            way[natural=moor];
            way["leisure"="nature_reserve"];
            
            rel[leisure=park];
            rel[landuse=recreation_ground];
            rel[leisure=recreation_ground];
            rel[leisure=pitch];
            rel[leisure=garden];
            rel[leisure=golf_course];
            rel[leisure=playground];
            rel[landuse=meadow];
            rel[landuse=grass];
            rel[landuse=greenfield];
            rel[natural=scrub];
            rel[natural=heath];
            rel[natural=grassland];
            rel[landuse=farmyard];
            rel[landuse=vineyard];
            rel[landuse=farmland];
            rel[landuse=orchard];
            rel[natural=plateau];
            rel[natural=moor];
            rel["leisure"="nature_reserve"];
        );
        out body;
        >;
        out skel qt;
        """
        query = query.format(date=date, bbox=bbox)
        response = requests.post(self.url, data=query)
        return response.json()

    def get_osm_data(self, date: str = '2019-02-24T00:00:00Z') -> List[dict]:
        """
        Gets the OpenStreetMap data for the given date and bounding box and saves it in the data folder.

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

        # Query the OpenStreetMap data for each bounding box
        osm_data = []
        for name, bbox in zip(self.names, self.bboxes):
            # Skip if the data already exists
            if os.path.exists(f'data/{name}.json'):
                logging.info(f'OpenStreetMap data for {name} already exists.')
                with open(f'data/{name}.json', 'r') as f:
                    osm_data.append(json.load(f))
                continue
            
            # Query the OpenStreetMap data
            logging.info(f'Querying OpenStreetMap data for {name} (this will take ages)...')
            _start = time.time()
            _osm_data = self._query_osm_data(bbox, date)
            osm_data.append(_osm_data)
            with open(f'data/{name}.json', 'w') as f:
                json.dump(_osm_data, f)
            _end = time.time()
            logging.info(f'Finished querying OpenStreetMap data for {name} in {_end - _start:.2f} seconds.')
        
        # Log the end of the process
        end = time.time()
        logging.info(f'Finished getting OpenStreetMap data in {end - start:.2f} seconds.')
        
        return osm_data
