#!/usr/bin/env python3


# +
# import(s)
# -
from typing import Any

import argparse
import pprint
import psycopg2
import os
import sys


# +
# constant(s)
# -
__doc__ = """python3 PsqlConnection.py --help"""

DB_AUTHORIZATION = f"artn:********"
DB_HOST = 'localhost'
DB_NAME = 'artn'
DB_PORT = 5432

DEF_COMMAND = "SELECT * FROM ObsReq2;"
FETCH_METHOD = ['fetchall', 'fetchone', 'fetchmany', 'raw']
FETCH_MANY = 5


# +
# class: PsqlConnection()
# -
class PsqlConnection(object):

    # +
    # method: __init__()
    # -
    def __init__(self, database: str = DB_NAME, authorization: str = DB_AUTHORIZATION,
            server: str = DB_HOST, port: int = DB_PORT):
        """ initialize the class """

        # get input(s)
        self.database = database
        self.authorization = authorization
        self.server = server
        self.port = port

        # private variable(s)
        self.__connection = None
        self.__cursor = None
        self.__connection_string = None
        self.__result = None
        self.__results = None

    # +
    # decorator(s)
    # -
    @property
    def database(self):
        return self.__database

    @database.setter
    def database(self, database: str = DB_NAME):
        self.__database = database if database.strip() == '' else DB_NAME

    @property
    def authorization(self):
        return self.__authorization

    @authorization.setter
    def authorization(self, authorization: str = DB_AUTHORIZATION):
        self.__authorization = authorization if ':' in authorization else DB_AUTHORIZATION
        self.__username, self.__password = self.__authorization.split(':')

    @property
    def server(self):
        return self.__server

    @server.setter
    def server(self, server: str = DB_HOST):
        self.__server = server if server.strip() == '' else DB_HOST

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port: int = DB_PORT):
        self.__port = port if port > 0 else DB_PORT

    # +
    # method: connect()
    # -
    def connect(self):
        """ connect to database """

        # set variable(s)
        self.__connection = None
        self.__cursor = None
        self.__connection_string = f"host='{self.server}' dbname='{self.database}' " \
            f"user='{self.__username}' password='{self.__password}'"

        # get connection
        try:
            self.__connection = psycopg2.connect(self.__connection_string)
        except Exception as _e1:
            self.__connection = None
            print(f"failed to connect to {self.database} on {self.server}:{self.port} with '{self.authorization}', error='{_e1}'")

        # get cursor
        try:
            self.__cursor = self.__connection.cursor()
        except Exception as _e2:
            self.__cursor = None
            print(f"failed to get cursor for {self.database} on {self.server}:{self.port} with '{self.authorization}', error='{_e1}'")

    # +
    # method: disconnect()
    # -
    def disconnect(self):
        """ disconnect from database """

        # disconnect cursor
        if self.__cursor is not None:
            self.__cursor.close()

        # disconnect connection
        if self.__connection is not None:
            self.__connection.close()

        # reset variable(s)
        self.__connection = None
        self.__cursor = None

    # +
    # method: fetchall()
    # -
    def fetchall(self, command: str = '') -> str:
        """ execute fetchall() command """

        # check input(s)
        if command.strip() == '' or self.__cursor is None:
            return ''

        # execute query
        try:
            self.__cursor.execute(command)
            self.__results = self.__cursor.fetchall()
            return self.__results
        except Exception as _:
            print(f"error in fetchall(), error='{_}'")
            return ''

    # +
    # method: fetchmany()
    # -
    def fetchmany(self, command: str = '', number: int = 0) -> str:
        """ execute fetchmany() command """

        # check input(s)
        if command.strip() == '' or number <= 0 or self.__cursor is None:
            return ''

        # execute query
        try:
            self.__cursor.execute(command)
            self.__results = self.__cursor.fetchall()
            return self.__results
        except Exception as _:
            print(f"error in fetchmany(), error='{_}'")
            return ''

    # +
    # method: fetchone()
    # -
    def fetchone(self, command: str = ''):
        """ execute fetchone() command """

        # check input(s)
        if command.strip() == '' or self.__cursor is None:
            return ''

        # execute query
        try:
            self.__cursor.execute(command)
            self.__result = self.__cursor.fetchall()
            return self.__result
        except Exception as _:
            print(f"error in fetchone(), error='{_}'")
            return ''


    # +
    # method: raw()
    # -
    def raw(self, command: str = ''):
        """ execute fetchone() command """

        # check input(s)
        if command.strip() == '' or self.__cursor is None:
            return ''

        # execute query
        try:
            self.__cursor.execute(command)
            self.__result = self.__cursor.fetchall()
            return self.__result
        except Exception as _:
            print(f"error in raw(), error='{_}'")
            return ''


# +
# function: psql_connection_test()
# -
def psql_connection_test(iargs: Any = None):

    # check input(s)
    if iargs is None:
        print(f"invalid input(s), iargs={iargs}")
        return
    print(f"iargs={iargs}")

    # get a command (edit default command as you see fit)
    _cmd = iargs.command.strip() == '' if iargs.command.strip() else DEF_COMMAND

    # instantiate class
    try:
        _t = PsqlConnection(iargs.database, iargs.authorization, iargs.server, iargs.port)
        print(f"_t={_t}")
        _t.connect()
        if iargs.method.lower() == 'fetchall':
            print(_t.fetchall(iargs.command))
        elif iargs.method.lower() == 'fetchone':
            print(_t.fetchone(iargs.command))
        elif iargs.method.lower() == 'fetchmany':
            print(_t.fetchmany(iargs.command, int(iargs.nelms)))
        elif iargs.method.lower() == 'raw':
            print(_t.raw(iargs.command))
        _t.disconnect()
    except:
        pass



# +
# main()
# -
if __name__ == '__main__':

    # get command line argument(s)
    _p = argparse.ArgumentParser(description=f'Test PostGresQL Database Connection', formatter_class=argparse.RawTextHelpFormatter)
    _p.add_argument(f'-a', f'--authorization', default=DB_AUTHORIZATION, help=f"""database authorization=<str>:<str>, defaults to '%(default)s'""")
    _p.add_argument(f'-c', f'--command', default='', help=f"""database command=<str>, defaults to '%(default)s'""")
    _p.add_argument(f'-d', f'--database', default=DB_NAME, help=f"""database name=<str>, defaults to '%(default)s'""")
    _p.add_argument(f'-m', f'--method', default=FETCH_METHOD[0], help=f"""database method=<str>, in {FETCH_METHOD} defaults to %(default)s""")
    _p.add_argument(f'-n', f'--nelms', default=FETCH_MANY, help=f"""database nelms=<int> (for fetchmany) defaults to %(default)s""")
    _p.add_argument(f'-p', f'--port', default=DB_PORT, help=f"""database port=<int>, defaults to %(default)s""")
    _p.add_argument(f'-s', f'--server', default=DB_HOST, help=f"""database server=<address>,  defaults to '%(default)s'""")
    args = _p.parse_args()

    # execute
    try:
        psql_connection_test(args)
    except Exception as _:
        print(f"{_}\n{__doc__}")
