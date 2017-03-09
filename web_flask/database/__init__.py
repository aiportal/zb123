from .fetch import *
from .zb123 import *


db_connections = [db_fetch, db_zb123]


class Database:
    @staticmethod
    def connect():
        for conn in db_connections:
            if conn.is_closed():
                conn.connect()

    @staticmethod
    def close():
        for conn in db_connections:
            if not conn.is_closed():
                conn.close()
