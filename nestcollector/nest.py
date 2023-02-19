"""
Module for creating the Nest class, which is used to store and processing the data from the Overpass API.
"""

import logging
import time

from .models import Nest as NestModel
from .osm_elements import Node, Relation, Way

from typing import List, Set, Tuple


class Nest:
    """
    Class for storing and processing the data from the Overpass API.

    Attributes:
        osm_data (List[dict]): The data from the Overpass API.
        area_names (List[str]): The names of the areas.
        nodes (Set[Node]): The nodes from the Overpass API data.
        ways (Set[Way]): The ways from the Overpass API data.
        relations (Set[Relation]): The relations from the Overpass API data.
        nodes_dict (Dict[int, Node]): The nodes from the Overpass API data as a dictionary.
        ways_dict (Dict[int, Way]): The ways from the Overpass API data as a dictionary.
    """

    def __init__(self, osm_data: List[dict], area_names: List[str]) -> None:
        """
        Initializes the Nest class.

        Args:
            osm_data (List[dict]): The data from the Overpass API.
            area_names (List[str]): The names of the areas.
        """
        self.osm_data = osm_data
        self.area_names = area_names
        self.nodes, self.ways, self.relations = self._get_osm_elements()
        self.nodes_dict = {node.id: node for node in self.nodes}
        self.ways_dict = {way.id: way for way in self.ways}
        self._build_polygons()

    def _build_polygons(self) -> None:
        """
        Builds the polygons of the ways and relations.
        """
        for way in self.ways:
            way.polygon = way.build_polygon(self.nodes_dict)
        for relation in self.relations:
            relation.multipolygon = relation.build_multipolygon(self.ways_dict)

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
                    relation = Relation(**element, area_name=area_name)
                    relations.add(relation)
                elif element['type'] == 'way':
                    way = Way(**element, area_name=area_name)
                    ways.add(way)
        end = time.time()
        logging.info(f'Found {len(nodes)} nodes, {len(ways)} ways, and {len(relations)} relations in {end - start:.2f} seconds.')
        return nodes, ways, relations

    def _get_nests_ways(self) -> List[NestModel]:
        """
        Gets the nests from the ways.

        Returns:
            List[NestModel]: The nests.
        """
        nests = []
        for way in self.ways:
            # Skip ways that don't have a polygon
            if way.polygon is None:
                continue
            nests.append(
                NestModel(
                    nest_id=way.id,
                    lat=way.polygon.centroid.y,
                    lon=way.polygon.centroid.x,
                    polygon=way.polygon,
                    area_name=way.area_name,
                    spawnpoints=None,
                    m2=way.area
                )
            )
        return nests

    def _get_nests_relations(self) -> List[NestModel]:
        """
        Gets the nests from the relations.

        Returns:
            List[NestModel]: The nests.
        """
        nests = []
        for relation in self.relations:
            # Skip relations that don't have a multipolygon
            if relation.multipolygon is None:
                continue
            nests.append(
                NestModel(
                    nest_id=relation.id,
                    lat=relation.multipolygon.centroid.y,
                    lon=relation.multipolygon.centroid.x,
                    polygon=relation.multipolygon,
                    area_name=relation.area_name,
                    spawnpoints=None,
                    m2=relation.area
                )
            )
        return nests
    
    def get_nests(self) -> List[NestModel]:
        """
        Gets the nests from the OSM elements.

        Returns:
            List[NestModel]: The nests.
        """
        nests = self._get_nests_ways()
        nests.extend(self._get_nests_relations())
        return nests
