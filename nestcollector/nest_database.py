"""
Module containing the NestDatabase class, which is used to connect to the database and store the nests.
"""
from .models import Base

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# MariaDB connection URI
SQLALCHEMY_DATABASE_URI = 'mariadb+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4'


class NestDatabase:
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
        engine = create_engine(connection_url)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
