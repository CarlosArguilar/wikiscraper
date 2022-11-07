'''
This module contains the functions to create the engine to communicate with Postgres,
and also to create sessions that will be used to send/retrieve data.
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .settings import settings

class DBConnection:

    def __init__(self):
        self.engine = self.get_engine()

    @classmethod
    def get_engine(cls):
        '''
        This method creates the engine used to communicate with the db and
        stores it in a class attribute, that can be used by all instances of the class 
        '''

        # Check if engine is already created, if so, returns it without creating a new one
        if hasattr(cls, '__engine'):
            return cls.__engine

        # Use info in settings.py file to create connection url
        url = "postgresql://{user}:{password}@{host}:{port}/{db}".format(**settings)

        engine = create_engine(url)

        cls.__engine = engine

        return cls.__engine

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()