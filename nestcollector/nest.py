"""
Module for creating the Nest class, which is used to store and processing the data from the Overpass API.
"""

import logging
import time

from .models import Nest as NestModel
from .osm_elements import Node, Relation, Way
from .timing import human_time

from typing import List, Set, Tuple


class Nest:
    """
    Class for storing and processing the data from the Overpass API.

    Attributes:
        osm_data (List[dict]): The data from the Overpass API.
        area_names (List[str]): The names of the areas.
        default_name (str): The default name of the nest.
        minimum_m2 (float): The minimum area in m2 to add a nest into the database.
        nodes (Set[Node]): The nodes from the Overpass API data.
        ways (Set[Way]): The ways from the Overpass API data.
        relations (Set[Relation]): The relations from the Overpass API data.
        nodes_dict (Dict[int, Node]): The nodes from the Overpass API data as a dictionary.
        ways_dict (Dict[int, Way]): The ways from the Overpass API data as a dictionary.
    """

    def __init__(
            self,
            osm_data: List[dict],
            area_names: List[str],
            default_name: str,
            minimum_m2: float
    ) -> None:
        """
        Initializes the Nest class.

        Args:
            osm_data (List[dict]): The data from the Overpass API.
            area_names (List[str]): The names of the areas.
            default_name (str): The default name of the nest.
            minimum_m2 (float): The minimum area in m2 to add a nest into the database.
        """
        self.osm_data = osm_data
        self.area_names = area_names
        self.default_name = default_name
        self.minimum_m2 = minimum_m2
        self.nodes, self.ways, self.relations = self._get_osm_elements()
        self.nodes_dict = {node.id: node for node in self.nodes}
        self.ways_dict = {way.id: way for way in self.ways}
        self._build_polygons()

    def _build_polygons(self) -> None:
        """
        Builds the polygons of the ways and relations.
        """
        logging.info('Building polygons...')
        start = time.time()
        for way in self.ways:
            way.polygon = way.build_polygon(self.nodes_dict)
        for relation in self.relations:
            relation.multipolygon = relation.build_multipolygon(self.ways_dict)
        end = time.time()
        logging.info(f'Polygons built in {human_time(end - start)}.')

    def _get_osm_elements(self) -> Tuple[Set[Node], Set[Way], Set[Relation]]:
        """
        Gets the OSM elements from the Overpass API data.

        Returns:
            Tuple[Set[Node], Set[Way], Set[Relation]]: The nodes, ways, and relations.
        """
        logging.info('Processing OSM elements...')
        start = time.time()
        nodes, ways, relations = set(), set(), set()
        for area, area_name in zip(self.osm_data, self.area_names):
            for element in area['elements']:
                if element['type'] == 'node':
                    node = Node(**element)
                    nodes.add(node)
                elif element['type'] == 'relation':
                    relation = Relation(**element, default_name=self.default_name, area_name=area_name)
                    relations.add(relation)
                elif element['type'] == 'way':
                    way = Way(**element, default_name=self.default_name, area_name=area_name)
                    ways.add(way)
        end = time.time()
        logging.info(f'Found {len(nodes)} nodes, {len(ways)} ways, and {len(relations)} relations in {human_time(end - start)}.')
        return nodes, ways, relations

    def _get_nests_ways(self) -> Tuple[List[NestModel], int, int, int]:
        """
        Gets the nests from the ways.

        Returns:
            Tuple[List[NestModel], int, int, int]: The nests, the number of invalid small and duplicated nests.
        """
        nests = []
        invalid_nests = 0
        small_nests = 0
        duplicated_nests = 0
        for way in self.ways:
            # Skip ways that don't have a polygon
            if way.polygon is None:
                invalid_nests += 1
                continue
            # Skip ways that are too small
            if way.area < self.minimum_m2:
                small_nests += 1
                continue
            # Skip ways that are duplicated in a relation
            if way.used_in_relation:
                duplicated_nests += 1
                continue
            nests.append(
                NestModel(
                    nest_id=way.id,
                    lat=way.polygon.centroid.y,
                    lon=way.polygon.centroid.x,
                    name=way.name,
                    polygon=way.polygon,
                    area_name=way.area_name,
                    spawnpoints=None,
                    m2=way.area
                )
            )
        return nests, invalid_nests, small_nests, duplicated_nests

    def _get_nests_relations(self) -> Tuple[List[NestModel], int, int]:
        """
        Gets the nests from the relations.

        Returns:
            Tuple[List[NestModel], int, int]: The nests, the number of invalid and small nests.
        """
        nests = []
        invalid_nests = 0
        small_nests = 0
        for relation in self.relations:
            # Skip relations that don't have a multipolygon
            if relation.multipolygon is None:
                invalid_nests += 1
                continue
            # Skip relations that are too small
            if relation.area < self.minimum_m2:
                small_nests += 1
                continue
            nests.append(
                NestModel(
                    nest_id=relation.id,
                    lat=relation.multipolygon.centroid.y,
                    lon=relation.multipolygon.centroid.x,
                    name=relation.name,
                    polygon=relation.multipolygon,
                    area_name=relation.area_name,
                    spawnpoints=None,
                    m2=relation.area
                )
            )
        return nests, invalid_nests, small_nests
    
    def get_nests(self) -> List[NestModel]:
        """
        Gets the nests from the OSM elements.

        Returns:
            List[NestModel]: The nests.
        """
        logging.info(f'Filtering nests...')
        start = time.time()
        nests_ways, invalid_ways, small_ways, duplicated_ways = self._get_nests_ways()
        nests_relations, invalid_relations, small_relations = self._get_nests_relations()
        nests = nests_ways + nests_relations
        invalid_nests = invalid_ways + invalid_relations
        small_nests = small_ways + small_relations
        end = time.time()
        logging.info(f'Filtered {invalid_nests} invalid nests, {small_nests} small nests ' \
                     f'and {duplicated_ways} duplicated nests in {human_time(end - start)}.')
        return nests
