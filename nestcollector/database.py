"""
Module containing the Database class, which is used to connect to the database and store the nests.
"""

import logging
import time

from .models import Base, Nest
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# MariaDB connection URI
SQLALCHEMY_DATABASE_URI = 'mariadb+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4'


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

    def save_nests(self, nests: List[Nest]) -> None:
        """
        Saves the nests to the database.

        Args:
            nests (List[Nest]): The nests to save.
        """
        logging.info(f'Saving {len(nests)} nests to database...')
        start = time.time()
        for nest in nests:
            self.db.merge(nest)
        self.db.commit()
        end = time.time()
        logging.info(f'Saved nests to database in {end - start:.2f} seconds.')
