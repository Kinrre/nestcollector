"""
Module containing model database definitions.
"""

from sqlalchemy import Column, Float, Index, String, func, text
from sqlalchemy.types import UserDefinedType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL, LONGTEXT, INTEGER, SMALLINT, TINYINT

Base = declarative_base()


class Geometry(UserDefinedType):
    """
    Represents a geometry column in the database.
    """

    def get_col_spec(self) -> str:
        """
        Returns the column specification.

        Returns:
            str: The column specification.
        """
        return 'GEOMETRY'

    def bind_expression(self, polygon) -> ColumnElement:
        """
        Given a polygon object, return the WKB representation of the polygon.

        Args:
            polygon: The polygon object.

        Returns:
            sqlalchemy.sql.expression.ColumnElement: The WKB representation of the polygon.
        """
        return func.ST_GeomFromText(polygon, type_=self)

    def column_expression(self, col) -> ColumnElement:
        """
        Given a SELECT column expression, return the WKT representation of the polygon.

        Args:
            col: The column expression.

        Returns:
            sqlalchemy.sql.expression.ColumnElement: The WKT representation of the polygon.
        """
        return func.ST_AsText(col, type_=self)


class Nest(Base):
    """
    Represents a nest in the database.
    """
    __tablename__ = 'nests'
    __table_args__ = (
        Index('CoordsIndex', 'lat', 'lon'),
    )

    nest_id = Column(BIGINT(20), primary_key=True)
    lat = Column(Float(18, True), nullable=False)
    lon = Column(Float(18, True), nullable=False)
    name = Column(String(250), nullable=False, server_default=text('"unknown"'))
    polygon_wkb = Column(Geometry, nullable=False)
    area_name = Column(String(250))
#    polygon_type = Column(TINYINT(1), nullable=False)
#    polygon_path = Column(LONGTEXT, nullable=False)
#    type = Column(TINYINT(1), nullable=False, server_default=text('0'))
    spawnpoints = Column(TINYINT(4), server_default=text('0'))
    m2 = Column(DECIMAL(10, 1), server_default=text('0.0'))
    updated = Column(INTEGER(10), index=True)
    pokemon_id = Column(INTEGER(11))
    pokemon_form = Column(SMALLINT(6))
    pokemon_avg = Column(Float(asdecimal=True))
    pokemon_ratio = Column(Float(asdecimal=True), server_default=text('0'))
    pokemon_count = Column(Float(asdecimal=True), server_default=text('0'))
    nest_submitted_by = Column(String(200))

    def __init__(
            self,
            nest_id: int,
            lat: float,
            lon: float,
            polygon_type: int,
            polygon_path: str,
            type: int,
            name: str,
            m2: float,
            area_name: str,
            polygon_wkb: str,
        ) -> None:
        """
        Initializes a new nest.

        Args:
            nest_id (int): The ID of the nest.
            lat (float): The latitude of the nest.
            lon (float): The longitude of the nest.
            polygon_type (int): The type of the polygon (0 Polygon and 1 MultiPolygon).
            polygon_path (str): The path of the polygon.
            type (int): The type of the nest (Unknown).
            name (str): The name of the nest.
            m2 (float): The area of the nest in m2.
            area_name (str): The name of the area.
            polygon_wkb (str): The WKB representation of the polygon.
        """
        self.nest_id = nest_id
        self.lat = lat
        self.lon = lon
        self.polygon_type = polygon_type
        self.polygon_path = polygon_path
        self.type = type
        self.name = name
        self.m2 = m2
        self.area_name = area_name
        self.polygon_wkb = polygon_wkb
