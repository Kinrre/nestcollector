"""
Module containing the Database class, which is used to connect to the database and store the nests.
"""

import logging
import time

from .models import Base, Nest

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List

# MariaDB connection URI
SQLALCHEMY_DATABASE_URI = 'mariadb+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4'

# SQL file for creating the stored procedure
NEST_PROCEDURE = './sql/get_nest_spawnpoints.sql'


class Database:
    """
    Class for connecting to the database and storing the nests.

    Attributes:
        db (sqlalchemy.orm.session.Session): The database session.
    """

    def __init__(
            self,
            host: str,
            port: str,
            name: str,
            user: str,
            password: str
        ) -> None:
        """
        Initializes the NestDatabase class.

        Args:
            host (str): The database host.
            port (str): The database port.
            name (str): The database name.
            user (str): The database user.
            password (str): The database password.
        """
        # Create ORM session and create the models if they don't exist
        connection_url = SQLALCHEMY_DATABASE_URI.format(
            host=host,
            port=port,
            name=name,
            user=user,
            password=password
        )
        engine = create_engine(connection_url, pool_pre_ping=True)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

    def call_spawnpoints_procedure(self) -> None:
        """
        Calls the stored procedure for counting the spawnpoints in a nest.
        """
        logging.info('Calculating and filtering spawnpoints of nests...')
        start = time.time()
        self.db.execute(text('CALL get_nest_spawnpoints()'))
        self.db.commit()
        end = time.time()
        logging.info(f'Calculated and filtering spawnpoints of nests in {end - start:.2f} seconds.')

    def create_spawnpoints_procedure(self, minimum_spawnpoints: int) -> None:
        """
        Creates the stored procedure for counting the spawnpoints in a nest.

        Args:
            minimum_spawnpoints (int): The minimum spawnpoints of a nest.
        """
        logging.info('Creating stored procedure for counting the spawnpoints in a nest...')
        self.db.execute(text(f'DROP PROCEDURE IF EXISTS get_nest_spawnpoints'))
        with open(NEST_PROCEDURE, 'r') as file:
            procedure = file.read()
            procedure = procedure.format(minimum_spawnpoints=minimum_spawnpoints)
        self.db.execute(text(procedure))

    def save_nests(self, nests: List[Nest]) -> None:
        """
        Saves the nests to the database deleting all previous nests.

        Args:
            nests (List[Nest]): The nests to save.
        """
        self.db.query(Nest).delete()
        logging.info('Deleted all nests from database.')
        logging.info(f'Saving {len(nests)} nests to database...')
        start = time.time()
        self.db.add_all(nests)
        self.db.commit()
        end = time.time()
        logging.info(f'Saved nests to database in {end - start:.2f} seconds.')
