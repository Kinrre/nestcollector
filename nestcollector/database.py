"""
Module containing the Database class, which is used to connect to the database and store the nests.
"""

import logging
import time

from .models import Base, Nest
from .timing import human_time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List

# MariaDB connection URI
SQLALCHEMY_DATABASE_URI = 'mariadb+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4'

# SQL file for creating the stored procedure
NEST_PROCEDURE = './sql/get_nest_spawnpoints.sql'
NEST_CHANSEY_PROCEDURE = './sql/get_nest_spawnpoints_chansey.sql'
NEST_OVERLAP_PROCEDURE = './sql/disable_overlapping_nests.sql'

class Database:
    """
    Class for connecting to the database and storing the nests.

    Attributes:
        db (sqlalchemy.orm.session.Session): The database session.
        use_chansey_db (bool): Whether to use the Chansey database.
        chansey_name (str): The Chansey database name.
        chansey_db (sqlalchemy.orm.session.Session): The Chansey database session.
    """

    def __init__(
            self,
            host: str,
            port: str,
            name: str,
            user: str,
            password: str,
            use_chansey_db: bool = False,
            chansey_host: str = None,
            chansey_port: str = None,
            chansey_name: str = None,
            chansey_user: str = None,
            chansey_password: str = None
        ) -> None:
        """
        Initializes the NestDatabase class.

        Args:
            host (str): The database host.
            port (str): The database port.
            name (str): The database name.
            user (str): The database user.
            password (str): The database password.
            use_chansey_db (bool): Whether to use the Chansey database.
            chansey_host (str): The Chansey database host.
            chansey_port (str): The Chansey database port.
            chansey_name (str): The Chansey database name.
            chansey_user (str): The Chansey database user.
            chansey_password (str): The Chansey database password.
        """
        self.db = self._create_session_local(host, port, name, user, password, create_tables=True)
        self.use_chansey_db = use_chansey_db
        if self.use_chansey_db:
            self.chansey_name = chansey_name
            self.chansey_db = self._create_session_local(chansey_host, chansey_port, chansey_name, chansey_user, chansey_password)

    def _create_session_local(self, host: str, port: str, name: str, user: str, password: str, create_tables: bool = False) -> None:
        """
        Creates the SQLAlchemy session.

        Args:
            host (str): The database host.
            port (str): The database port.
            name (str): The database name.
            user (str): The database user.
            password (str): The database password.
            create_tables (bool, Optional): Whether to create the tables if they don't exist. Default to False.
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
        if create_tables:
            Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()

    def multi_to_poly(self) -> None:
        """
        Converts all multipolygon to polygon.
        """
        logging.info('Overwriting multipolygon as polygon...')
        start = time.time()
        self.db.execute(text('update nests set polygon=ST_CONVEXHULL(polygon) where left(astext(polygon),5) = "MULTI"'))
        self.db.commit()
        end = time.time()
        logging.info(f'Converted all multipolygon to polygon in {human_time(end - start)}.')

    def call_spawnpoints_procedure(self) -> None:
        """
        Calls the stored procedure for counting the spawnpoints in a nest.
        """
        logging.info('Calculating and filtering spawnpoints of nests...')
        start = time.time()
        self.db.execute(text('CALL get_nest_spawnpoints()'))
        self.db.commit()
        end = time.time()
        logging.info(f'Calculated and filtering spawnpoints of nests in {human_time(end - start)}.')

    def create_spawnpoints_procedure(self, minimum_spawnpoints: int) -> None:
        """
        Creates the stored procedure for counting the spawnpoints in a nest.

        Args:
            minimum_spawnpoints (int): The minimum spawnpoints of a nest.
        """
        logging.info('Creating stored procedure for counting the spawnpoints in a nest...')
        self.db.execute(text(f'DROP PROCEDURE IF EXISTS get_nest_spawnpoints'))
        if self.use_chansey_db:
            with open(NEST_CHANSEY_PROCEDURE, 'r') as file:
                procedure = file.read()
                procedure = procedure.format(chansey_db=self.chansey_name, minimum_spawnpoints=minimum_spawnpoints)
        else:
            with open(NEST_PROCEDURE, 'r') as file:
                procedure = file.read()
                procedure = procedure.format(minimum_spawnpoints=minimum_spawnpoints)
        self.db.execute(text(procedure))

    def call_filtering_procedure(self) -> None:
        """
        Calls the stored procedure for filtering overlapping nests.
        """
        logging.info('Disabling overlapping nests...')
        start = time.time()
        self.db.execute(text('CALL nest_filter_overlap()'))
        self.db.commit()
        end = time.time()
        logging.info(f'Disabled overlapping nests {human_time(end - start)}.')

    def create_filtering_procedure(self, maximum_overlap: int) -> None:
        """
        Creates the stored procedure for filtering overlapping nests.

        Args:
            maximum_overlap (int): The maximum allowed overlap between nests.
        """
        logging.info('Creating stored procedure for overlapping nest filtering...')
        self.db.execute(text(f'DROP PROCEDURE IF EXISTS nest_filter_overlap'))
        with open(NEST_OVERLAP_PROCEDURE, 'r') as file:
            procedure = file.read()
            procedure = procedure.format(maximum_overlap=maximum_overlap)
        self.db.execute(text(procedure))

    def count_active_nests(self) -> int:
        """
        Counts the active nests in the database.

        Returns:
            int: The number of active nests in the database.
        """
        count = self.db.query(Nest).filter(Nest.active == True).count()
        return count

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
        logging.info(f'Saved nests to database in {human_time(end - start)}.')
