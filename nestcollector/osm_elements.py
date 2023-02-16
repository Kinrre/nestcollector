"""
Module containing the OSMElements class, which is used to parse OSM elements from the Overpass API.
"""

from typing import List, Optional


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
    """

    def __init__(self, type: str, id: int, nodes: List[int], tags: Optional[dict] = None) -> None:
        """
        Initializes the Way class.

        Args:
            type (str): The type of the element.
            id (int): The ID of the element.
            nodes (List[int]): The nodes of the way.
            tags (Optional[dict]): The tags of the element.
        """
        self.type = type
        self.id = id
        self.nodes = nodes
        self.tags = tags

    def __eq__(self, other: 'Way') -> bool:
        """
        Checks if two ways are equal, by comparing their IDs.

        Args:
            other (Way): The other way.

        Returns:
            bool: True if the ways are equal, False otherwise.
        """
        return isinstance(other, Way) and self.id == other.id

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
    """

    def __init__(self, type: str, id: int, members: List[dict], tags: Optional[dict] = None) -> None:
        """
        Initializes the Relation class.

        Args:
            type (str): The type of the element.
            id (int): The ID of the element.
            members (List[dict]): The members of the relation.
            tags (Optional[dict]): The tags of the element.
        """
        self.type = type
        self.id = id
        self.members = members
        self.tags = tags

    def __eq__(self, other: 'Relation') -> bool:
        """
        Checks if two relations are equal, by comparing their IDs.

        Args:
            other (Relation): The other relation.
        """
        return isinstance(other, Relation) and self.id == other.id

    def __str__(self) -> str:
        """
        Returns a string representation of the relation.

        Returns:
            str: The string representation of the relation.
        """
        return f'Relation(id={self.id}, members={self.members}, tags={self.tags})'
