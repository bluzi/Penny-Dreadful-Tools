import apsw

from magic import card
from shared import configuration
from shared.pd_exception import DatabaseException

class Database:
    def __init__(self, location):
        try:
            self.connection = apsw.Connection(location)
            self.connection.setrowtrace(row_factory)
            self.connection.enableloadextension(True)
            self.connection.loadextension(configuration.get('spellfix'))
            self.connection.createscalarfunction('unaccent', card.unaccent, 1)
            self.cursor = self.connection.cursor()
        except apsw.Error as e:
            raise DatabaseException('Failed to initialized database in `{location}`'.format(location=location)) from e

    def execute(self, sql, args=None):
        if args is None:
            args = []
        try:
            return self.cursor.execute(sql, args).fetchall()
        except apsw.Error as e:
            raise DatabaseException('Failed to execute `{sql}` because of `{e}`'.format(sql=sql, e=e))from e

    def value(self, sql, args=None, default=None, fail_on_missing=False):
        try:
            return self.values(sql, args)[0]
        except IndexError as e:
            if fail_on_missing:
                raise DatabaseException('Failed to get a value from `{sql}`'.format(sql=sql)) from e
            else:
                return default

    def values(self, sql, args=None):
        rs = self.execute(sql, args)
        return [list(row.values())[0] for row in rs]

    def insert(self, sql, args=None):
        self.execute(sql, args)
        return self.value('SELECT last_insert_rowid()')

def row_factory(cursor, row):
    columns = [t[0] for t in cursor.getdescription()]
    return dict(zip(columns, row))

def sqlescape(s) -> str:
    if str(s).isdecimal():
        return s
    encodable = s.encode('utf-8', 'strict').decode('utf-8')
    if encodable.find('\x00') >= 0:
        raise Exception('NUL not allowed in SQL string.')
    return "'{escaped}'".format(escaped=encodable.replace("'", "''"))

def sqllikeescape(s):
    s = s.replace('%', '\\%').replace('_', '\\_')
    return sqlescape('%{s}%'.format(s=s))