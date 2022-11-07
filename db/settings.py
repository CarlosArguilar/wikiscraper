'''
The setting to access the database will be stored in this dict for the sake of simplicity,
but be aware that this is not a recommended practice and for a production enviroment it should
be used other (more reliable) methods for storing credentials.
'''
settings = {
    'user':'postgres',
    'password':'postgres',
    'host':'127.0.0.1',
    'port':5432,
    'db': 'mockdb'
    }