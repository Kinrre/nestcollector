"""
Module containing model database definitions.
"""

from sqlalchemy import Column, Float, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL, LONGTEXT, INTEGER, SMALLINT, TINYINT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Nest(Base):
    """
    Represents a nest in the database.
    """
    __tablename__ = 'nest'
    __table_args__ = (
        Index('CoordsIndex', 'lat', 'lon'),
    )

    nest_id = Column(BIGINT(20), primary_key=True)
    lat = Column(Float(18, True), nullable=False)
    lon = Column(Float(18, True), nullable=False)
    polygon_type = Column(TINYINT(1), nullable=False)
    polygon_path = Column(LONGTEXT, nullable=False)
    type = Column(TINYINT(1), nullable=False, server_default=text('0'))
    name = Column(String(250))
    spawnpoints = Column(TINYINT(4), server_default=text('0'))
    m2 = Column(DECIMAL(10, 1), server_default=text('0.0'))
    updated = Column(INTEGER(10), index=True)
    pokemon_id = Column(INTEGER(11))
    pokemon_form = Column(SMALLINT(6))
    pokemon_avg = Column(Float(asdecimal=True))
    pokemon_ratio = Column(Float(asdecimal=True), server_default=text('0'))
    pokemon_count = Column(Float(asdecimal=True), server_default=text('0'))
    nest_submitted_by = Column(String(200))
