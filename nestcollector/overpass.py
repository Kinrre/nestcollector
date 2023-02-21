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
        coords (List[str]): The coordinates to query.
    """

    def __init__(self, areas_path: str) -> None:
        """
        Initializes the Overpass class.

        Args:
            areas_path (str): The path to the areas GeoJSON file.
        """
        self.url = 'https://overpass.kumi.systems/api/interpreter'
        self.area_names = self._get_names(areas_path)
        self.polygons = self._load_polygons(areas_path)
        self.coords = self._get_coords()

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

    def _get_coords(self) -> List[str]:
        """
        Gets the coordinates of the polygons.

        Returns:
            List[str]: The coordinates to query.
        """
        coords = []
        for polygon in self.polygons:
            _coords = []
            for lat, lon in polygon.exterior.coords:
                _coords.append(f'{lat} {lon}')
            _coords = ' '.join(_coords)
            coords.append(_coords)
        return coords

    def _query_osm_data(self, coords: str, date: str = '2019-02-24T00:00:00Z') -> dict:
        """
        Queries the OpenStreetMap data for the given date and coords.

        Args:
            coords (str): The coords to query.
            date (str, optional): The date to query. Defaults to '2019-02-24T00:00:00Z'.

        Returns:
            dict: The response from the Overpass API.
        """
        query = """
        [out:json]
        [date:"{date}"]
        [timeout:100000];
        (
            way[leisure=park](poly:"{coords}");
            way[landuse=recreation_ground](poly:"{coords}");
            way[leisure=recreation_ground](poly:"{coords}");
            way[leisure=pitch](poly:"{coords}");
            way[leisure=garden](poly:"{coords}");
            way[leisure=golf_course](poly:"{coords}");
            way[leisure=playground](poly:"{coords}");
            way[landuse=meadow](poly:"{coords}");
            way[landuse=grass](poly:"{coords}");
            way[landuse=greenfield](poly:"{coords}");
            way[natural=scrub](poly:"{coords}");
            way[natural=heath](poly:"{coords}");
            way[natural=grassland](poly:"{coords}");
            way[landuse=farmyard](poly:"{coords}");
            way[landuse=vineyard](poly:"{coords}");
            way[landuse=farmland](poly:"{coords}");
            way[landuse=orchard](poly:"{coords}");
            way[natural=plateau](poly:"{coords}");
            way[natural=moor](poly:"{coords}");
            way["leisure"="nature_reserve"](poly:"{coords}");
            
            rel[leisure=park](poly:"{coords}");
            rel[landuse=recreation_ground](poly:"{coords}");
            rel[leisure=recreation_ground](poly:"{coords}");
            rel[leisure=pitch](poly:"{coords}");
            rel[leisure=garden](poly:"{coords}");
            rel[leisure=golf_course](poly:"{coords}");
            rel[leisure=playground](poly:"{coords}");
            rel[landuse=meadow](poly:"{coords}");
            rel[landuse=grass](poly:"{coords}");
            rel[landuse=greenfield](poly:"{coords}");
            rel[natural=scrub](poly:"{coords}");
            rel[natural=heath](poly:"{coords}");
            rel[natural=grassland](poly:"{coords}");
            rel[landuse=farmyard](poly:"{coords}");
            rel[landuse=vineyard](poly:"{coords}");
            rel[landuse=farmland](poly:"{coords}");
            rel[landuse=orchard](poly:"{coords}");
            rel[natural=plateau](poly:"{coords}");
            rel[natural=moor](poly:"{coords}");
            rel["leisure"="nature_reserve"](poly:"{coords}");
        );
        out body;
        >;
        out skel qt;
        """
        query = query.format(date=date, coords=coords)
        valid_response = False
        osm_data = None
        # Retry if the response is invalid
        while not valid_response:
            response = requests.post(self.url, data=query)
            if response.status_code == 200:
                valid_response = True
                osm_data = response.json()
            else:
                logging.warning(f'Invalid response code: {response.status_code}. Retrying in 30 seconds...')
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
        for name, coords in zip(self.area_names, self.coords):
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
