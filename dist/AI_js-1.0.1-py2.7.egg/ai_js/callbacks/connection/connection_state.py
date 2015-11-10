"""
Provides class to maintain data persistence for each active websocket connection.
"""


from anser_indicus.data.meta_database import MetaDatabase
from anser_indicus.utilities.progress import Progress
from anser_indicus.data.queryable_database import QueryableDatabase
from anser_indicus.data.database_pool import DatabasePool


class ConnectionState(object):
    """
    Maintains connections to databases for client on the other end of a websocket connection.

    :ivar databasepool: (:py:class:`anser_indicus.data.database_pool.DatabasePool`) Connection-wide pool
                        from which to create new database connections. Isolates
                        current user's connections from another user on the same server.
    :ivar metadb: (:py:class:`anser_indicus.data.meta_database.MetaDatabase`)
                  connection to the AnserIndicus MetaDatabase. Gets information about all databases "installed" on
                  server.
    :ivar func messagewriter: Function that API can use to write websocket messages to the client
    :ivar progress: (:py:class:`anser_indicus.utilities.progress.AIProgressv2`)
                    AnserIndicus progress bar object. Optional.
    :ivar dict data: Data storage that can be exploited by custom application to save state
    :ivar db: (:py:class:`anser_indicus.data.queryable_database.QueryableDatabase`) An active database connection
    """
    def __init__(self, messagewriter=None):
        """
        :keyword func messagewriter: function to call to write messages over websocket.
        """
        self.databasepool = DatabasePool()
        self.metadb = MetaDatabase(pool=self.databasepool)
        self.messagewriter = messagewriter
        self.data = {}  # connection-level variables can be stored here
        self.progress = Progress(num_updates=150)   # override self.progress.on_update to control visualization
        self.db = None
            
    def close(self):
        """
        Close connection to meta database.

        .. note:: No longer necessary, Python garbage collection should take care of this automatically
        """
        self.metadb.close()
            
    def connect_database(self, dbname=""):
        """
        Connect a database and add it to the internal list of open databases

        .. note:: Specified database must be stored within the `anser_indicus` `DATA_PATH` on the server.
        :keyword str dbname: name of the database to connect to.
        """
        print "CONNECTING ", dbname
        self.db = QueryableDatabase(dbname, pool=self.databasepool)

    def is_database_open(self):
        """
        Check if a database is open already, a precondition for some functions.

        :return: True if open, False if not.
        :rtype: bool
        """
        if self.db is not None and self.db.is_configured:
            print "Database is open"
            return True
        else:
            if self.db is None:
                print "Database is none"
            print "Database is not open"
            return False
