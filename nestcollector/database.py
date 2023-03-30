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
NEST_SPAWNPOINTS_PROCEDURE = './sql/get_nest_spawnpoints.sql'
NEST_OVERLAPPING_PROCEDURE = './sql/disable_overlapping_nests.sql'
NEST_STATS_SPAWNPOINTS_PROCEDURE = './sql/stats/get_nest_spawnpoints.sql'
NEST_STATS_LOW_COVERAGE_PROCEDURE = './sql/stats/disable_low_coverage_nests.sql'


class Database:
    """
    Class for connecting to the database and storing the nests.

    Attributes:
        db (sqlalchemy.orm.session.Session): The database session.
        use_stats_db (bool): Whether to use the Stats database.
        stats_name (str): The Stats database name.
        stats_db (sqlalchemy.orm.session.Session): The Stats database session.
    """

    def __init__(
            self,
            host: str,
            port: str,
            name: str,
            user: str,
            password: str,
            use_stats_db: bool = False,
            stats_host: str = None,
            stats_port: str = None,
            stats_name: str = None,
            stats_user: str = None,
            stats_password: str = None
        ) -> None:
        """
        Initializes the NestDatabase class.

        Args:
            host (str): The database host.
            port (str): The database port.
            name (str): The database name.
            user (str): The database user.
            password (str): The database password.
            use_stats_db (bool): Whether to use the Stats database.
            stats_host (str): The Stats database host.
            stats_port (str): The Stats database port.
            stats_name (str): The Stats database name.
            stats_user (str): The Stats database user.
            stats_password (str): The Stats database password.
        """
        self.db = self._create_session_local(host, port, name, user, password, create_tables=True)
        self.use_stats_db = use_stats_db
        if self.use_stats_db:
            self.stats_name = stats_name
            self.stats_db = self._create_session_local(stats_host, stats_port, stats_name, stats_user, stats_password)

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

    def call_low_coverage_procedure(self) -> None:
        """
        Calls the stored procedure for filtering low coverage nests by mon area.
        """
        logging.info('Disabling low coverage by mon area nests...')
        start = time.time()
        self.db.execute(text('CALL nest_filter_low_coverage()'))
        self.db.commit()
        end = time.time()
        count = self.db.query(Nest).filter(Nest.discarded == 'low_coverage').count()
        logging.info(f'Disabled {count} low coverage by mon area nests in {human_time(end - start)}.')

    def create_low_coverage_procedure(self, minimum_coverage: int) -> None:
        """
        Creates the stored procedure for filtering low coverage nests by mon area.

        Args:
            minimum_coverage (int): The minimum coverage of a nest by mon area.
        """
        self.db.execute(text(f'DROP PROCEDURE IF EXISTS nest_filter_low_coverage'))
        with open(NEST_STATS_LOW_COVERAGE_PROCEDURE, 'r') as file:
            procedure = file.read()
            procedure = procedure.format(stats_db=self.stats_name, minimum_coverage=minimum_coverage)
        self.db.execute(text(procedure))

    def call_spawnpoints_procedure(self) -> None:
        """
        Calls the stored procedure for counting the spawnpoints in a nest.
        """
        logging.info('Calculating and filtering spawnpoints of nests...')
        start = time.time()
        self.db.execute(text('CALL get_nest_spawnpoints()'))
        self.db.commit()
        end = time.time()
        count = self.db.query(Nest).filter(Nest.discarded == 'spawnpoints').count()
        logging.info(f'Disabled {count} nests due to low number of spawnpoints in {human_time(end - start)}.')

    def create_spawnpoints_procedure(self, minimum_spawnpoints: int) -> None:
        """
        Creates the stored procedure for counting the spawnpoints in a nest.

        Args:
            minimum_spawnpoints (int): The minimum spawnpoints of a nest.
        """
        self.db.execute(text(f'DROP PROCEDURE IF EXISTS get_nest_spawnpoints'))
        if self.use_stats_db:
            with open(NEST_STATS_SPAWNPOINTS_PROCEDURE, 'r') as file:
                procedure = file.read()
                procedure = procedure.format(stats_db=self.stats_name, minimum_spawnpoints=minimum_spawnpoints)
        else:
            with open(NEST_SPAWNPOINTS_PROCEDURE, 'r') as file:
                procedure = file.read()
                procedure = procedure.format(minimum_spawnpoints=minimum_spawnpoints)
        self.db.execute(text(procedure))

    def call_overlappping_procedure(self) -> None:
        """
        Calls the stored procedure for filtering overlapping nests.
        """
        logging.info('Disabling overlapping nests...')
        start = time.time()
        self.db.execute(text('CALL nest_filter_overlap()'))
        self.db.commit()
        end = time.time()
        count = self.db.query(Nest).filter(Nest.discarded == 'overlap').count()
        logging.info(f'Disabled {count} overlapping nests in {human_time(end - start)}.')

    def create_overlapping_procedure(self, maximum_overlap: int) -> None:
        """
        Creates the stored procedure for filtering overlapping nests.

        Args:
            maximum_overlap (int): The maximum allowed overlap between nests.
        """
        self.db.execute(text(f'DROP PROCEDURE IF EXISTS nest_filter_overlap'))
        with open(NEST_OVERLAPPING_PROCEDURE, 'r') as file:
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
