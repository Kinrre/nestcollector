"""
Module for creating the Nest class, which is used to store and process the data from the Overpass API.
"""

import logging
import time

from .models import Nest as NestModel
from .osm_elements import Node, Relation, Way

from typing import List, Tuple

# Polygon types
POLYGON = 0
MULTIPOLYGON = 1


class Nest:

    def __init__(self, osm_data: List[dict]) -> None:
        """
        Initializes the Nest class.

        Args:
            osm_data (List[dict]): The data from the Overpass API.
        """
        self.osm_data = osm_data
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

    def _get_osm_elements(self) -> Tuple[List[Node], List[Way], List[Relation]]:
        """
        Gets the OSM elements from the Overpass API data.

        Returns:
            Tuple[List[Node], List[Way], List[Relation]]: The nodes, ways, and relations.
        """
        logging.info('Processing OSM elements...')
        start = time.time()
        nodes, ways, relations = [], [], []
        for area in self.osm_data:
            for element in area['elements']:
                if element['type'] == 'node':
                    node = Node(**element)
                    if node not in nodes:
                        nodes.append(node)
                elif element['type'] == 'relation':
                    relation = Relation(**element)
                    if relation not in relations:
                        relations.append(relation)
                elif element['type'] == 'way':
                    way = Way(**element)
                    if way not in ways:
                        ways.append(way)
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
            nests.append(
                NestModel(
                    nest_id=way.id,
                    lat=0,
                    lon=0,
                    polygon_type=POLYGON,
                    polygon_path='',
                    type=0,
                    name=way.name,
                    polygon_wkb=way.polygon
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
            nests.append(
                NestModel(
                    nest_id=relation.id,
                    lat=0,
                    lon=0,
                    polygon_type=MULTIPOLYGON,
                    polygon_path='',
                    type=0,
                    name=relation.name,
                    polygon_wkb=relation.multipolygon
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
