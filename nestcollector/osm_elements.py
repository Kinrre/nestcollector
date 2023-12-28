"""
Module containing the OSMElements class, which is used to parse OSM elements from the Overpass API.
"""

from pyproj import Geod
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import orient
from typing import List, Mapping, Optional, Union


class Node:
    """
    Represents an OSM node.

    Attributes:
        type (str): The type of the element.
        id (int): The ID of the element.
        lat (float): The latitude of the node.
        lon (float): The longitude of the node.
        tags (Optional[dict]): The tags of the element.
    """

    def __init__(self, type: str, id: int, lat: float, lon: float, tags: Optional[dict] = None) -> None:
        """
        Initializes the Node class.

        Args:
            type (str): The type of the element.
            id (int): The ID of the element.
            lat (float): The latitude of the node.
            lon (float): The longitude of the node.
            tags (Optional[dict]): The tags of the element.
        """
        self.type = type
        self.id = id
        self.lat = lat
        self.lon = lon
        self.tags = tags

    def __eq__(self, other: 'Node') -> bool:
        """
        Checks if two nodes are equal, by comparing their IDs.

        Args:
            other (Node): The other node.
        
        Returns:
            bool: True if the nodes are equal, False otherwise.
        """
        return isinstance(other, Node) and self.id == other.id

    def __hash__(self) -> int:
        """
        Returns the hash of the node.

        Returns:
            int: The hash of the node.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        Returns a string representation of the node.

        Returns:
            str: The string representation of the node.
        """
        return f'Node(id={self.id}, lat={self.lat}, lon={self.lon}, tags={self.tags})'


class Way:
    """
    Represents an OSM way.

    Attributes:
        type (str): The type of the element.
        id (int): The ID of the element.
        nodes (List[int]): The nodes of the way.
        tags (Optional[dict]): The tags of the element.
        name (Optional[str]): The name of the way.
        polygon (Optional[Polygon]): The polygon of the way.
        area (Optional[float]): The area in m2 of the way.
        area_name (Optional[str]): The name of the area the way belongs.
        used_in_relation (bool): Whether the way is used in a relation.
    """

    def __init__(
            self,
            type: str,
            id: int,
            nodes: List[int],
            tags: Optional[dict] = None,
            default_name: Optional[str] = None,
            area_name: Optional[str] = None
        ) -> None:
        """
        Initializes the Way class.

        Args:
            type (str): The type of the element.
            id (int): The ID of the element.
            nodes (List[int]): The nodes of the way.
            tags (Optional[dict]): The tags of the element.
            default_name (Optional[str]): The default name of the way.
            area_name (Optional[str]): The name of the area the way belongs.
        """
        self.type = type
        self.id = id
        self.nodes = nodes
        self.tags = tags
        self.name = tags['name'] if tags and 'name' in tags else default_name
        self.polygon = None
        self._area = None
        self.area_name = area_name
        self.used_in_relation = False

    @property
    def area(self) -> float:
        """
        Returns the area in m2 of the way.

        Returns:
            float: The area in m2 of the way.
        """
        if self.polygon is None:
            self.polygon = self.build_polygon()
        if self._area is None:
            geod = Geod(ellps='WGS84')
            self._area = geod.geometry_area_perimeter(self.polygon)[0]
        return self._area

    def build_polygon(self, nodes: Mapping[int, Node]) -> Polygon:
        """
        Builds a polygon from the way's nodes.

        Args:
            nodes (Mapping[int, Node]): The nodes of the way.

        Returns:
            Polygon: The polygon of the way.
        """
        # Check that the nodes defining the way are in the nodes dict
        # If any of the nodes is not in the dict, remove that node from the way
        self.nodes = [node for node in self.nodes if node in nodes]
        # Check if the way has at least 3 nodes
        if len(self.nodes) < 3:
            return None
        polygon = Polygon([(nodes[node].lon, nodes[node].lat) for node in self.nodes])
        polygon = orient(polygon) # Orient the polygon to compute the m2 area
        return polygon

    def __eq__(self, other: 'Way') -> bool:
        """
        Checks if two ways are equal, by comparing their IDs.

        Args:
            other (Way): The other way.

        Returns:
            bool: True if the ways are equal, False otherwise.
        """
        return isinstance(other, Way) and self.id == other.id

    def __hash__(self) -> int:
        """
        Returns the hash of the way.

        Returns:
            int: The hash of the way.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        Returns a string representation of the way.

        Returns:
            str: The string representation of the way.
        """
        return f'Way(id={self.id}, nodes={self.nodes}, tags={self.tags})'


class Relation:
    """
    Represents an OSM relation.

    Attributes:
        type (str): The type of the element.
        id (int): The ID of the element.
        members (List[dict]): The members of the relation.
        tags (Optional[dict]): The tags of the element.
        name (Optional[str]): The name of the relation.
        multipolygon (Optional[MultiPolygon]): The multipolygon of the relation.
        area (Optional[float]): The area in m2 of the relation.
        area_name (Optional[str]): The name of the area the relation belongs.
    """

    def __init__(
            self,
            type: str,
            id: int,
            members: List[dict],
            tags: Optional[dict] = None,
            default_name: Optional[str] = None,
            area_name: Optional[str] = None
        ) -> None:
        """
        Initializes the Relation class.

        Args:
            type (str): The type of the element.
            id (int): The ID of the element.
            members (List[dict]): The members of the relation.
            tags (Optional[dict]): The tags of the element.
            default_name (Optional[str]): The default name of the relation.
            area_name (Optional[str]): The name of the area the relation belongs.
        """
        self.type = type
        self.id = id
        self.members = members
        self.tags = tags
        self.name = tags['name'] if tags and 'name' in tags else default_name
        self.multipolygon = None
        self._area = None
        self.area_name = area_name

    @property
    def area(self) -> float:
        """
        Returns the area in m2 of the way.

        Returns:
            float: The area in m2 of the way.
        """
        if self.multipolygon is None:
            self.multipolygon = self.build_multipolygon()
        if self._area is None:
            geod = Geod(ellps='WGS84')
            self._area = geod.geometry_area_perimeter(self.multipolygon)[0]
        return self._area

    def build_multipolygon(self, ways: Mapping[int, Way], buffer: bool = False) -> Union[MultiPolygon, Polygon]:
        """
        Builds a multipolygon from the relation's ways.

        It builds a multipolygon from the outer ways of the relation, if there are
        no outer ways, from the ways with no role, and if there are no ways with
        no role,from the inner ways of the relation, else it returns None.

        Args:
            ways (Mapping[int, Way]): The ways of the relation.
            buffer (Optional[bool]): Whether to buffer the multipolygon or not. Defaults to False.

        Returns:
            MultiPolygon: The multipolygon of the relation.
        """
        # NOTE: Perimeter ways must be ignored according to the OSM wiki
        polygons = {'outer': [], '': [], 'inner': []}
        for member in self.members:
            if member['type'] == 'way':
                way = ways.get(member['ref'])
                # Check if the way is in the ways dict
                if not way:
                    continue
                way.used_in_relation = True
                if way.polygon is None:
                    polygon = way.build_polygon(ways)
                    # Check if the way is a polygon
                    if polygon is None:
                        continue
                    way.polygon = polygon
                # Add the polygon to the corresponding list of polygons
                if member['role'] in polygons:
                    polygons[member['role']].append(way.polygon)

        # Check if the relation has at least one 
        if len(polygons['outer']) > 0:
            polygons = polygons['outer']
        elif len(polygons['']) > 0:
            polygons = polygons['']
        elif len(polygons['inner']) > 0:
            polygons = polygons['inner']
        else:
            return None

        multipolygon = MultiPolygon(polygons)
        if buffer:
            multipolygon = multipolygon.buffer(1e-4) # As OSM data is not perfect, we need to buffer the multipolygon
        multipolygon = orient(multipolygon) # Orient the multipolygon to compute the m2 area
        return multipolygon

    def __eq__(self, other: 'Relation') -> bool:
        """
        Checks if two relations are equal, by comparing their IDs.

        Args:
            other (Relation): The other relation.
        """
        return isinstance(other, Relation) and self.id == other.id

    def __hash__(self) -> int:
        """
        Returns the hash of the relation.

        Returns:
            int: The hash of the relation.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        Returns a string representation of the relation.

        Returns:
            str: The string representation of the relation.
        """
        return f'Relation(id={self.id}, members={self.members}, tags={self.tags})'
