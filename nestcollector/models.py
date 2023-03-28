"""
Module containing model database definitions.
"""

from sqlalchemy import Column, Float, Index, String, func, text
from sqlalchemy.types import UserDefinedType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL, INTEGER, SMALLINT, TINYINT

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

    nest_id = Column(BIGINT(20), primary_key=True, autoincrement=False)
    lat = Column(Float(18, True), nullable=False)
    lon = Column(Float(18, True), nullable=False)
    name = Column(String(250), nullable=False, server_default=text('"unknown"')) # TODO: Make this configurable
    polygon = Column(Geometry, nullable=False)
    area_name = Column(String(250))
    spawnpoints = Column(SMALLINT(unsigned=True), server_default=text('0'))
    m2 = Column(DECIMAL(10, 1), server_default=text('0.0'))
    active = Column(TINYINT(1), server_default=text('0'))
    pokemon_id = Column(INTEGER(11))
    pokemon_form = Column(SMALLINT(6))
    pokemon_avg = Column(Float(asdecimal=True))
    pokemon_ratio = Column(Float(asdecimal=True), server_default=text('0'))
    pokemon_count = Column(Float(asdecimal=True), server_default=text('0'))
    discarded = Column(String(40))
    updated = Column(INTEGER(10), index=True)

    def __init__(
            self,
            nest_id: int,
            lat: float,
            lon: float,
            name: str,
            polygon: Geometry,
            area_name: str,
            spawnpoints: int,
            m2: float
        ) -> None:
        """
        Initializes a new nest.

        Args:
            nest_id (int): The ID of the nest.
            lat (float): The latitude of the nest.
            lon (float): The longitude of the nest.
            name (str): The name of the nest.
            polygon (Geometry): The polygon of the nest.
            area_name (str): The name of the area.
            spawnpoints (int): The number of spawnpoints in the nest.
            m2 (float): The area of the nest in square meters.
        """
        self.nest_id = nest_id
        self.lat = lat
        self.lon = lon
        self.name = name
        self.polygon = polygon
        self.area_name = area_name
        self.spawnpoints = spawnpoints
        self.m2 = m2
