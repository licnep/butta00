"""
Connect to a database, and list available databases on server

:precondition: On server, ``anser_indicus`` must be installed, databases saved in path pointed to by
              ``anser_indicus.config_settings.DATA_PATH``, and database must be configured by running
              ``setup_dataset.py``, an executable script provided by ``anser_indicus``.

"""

from ai_js.callbacks.connection.connection_state import ConnectionState


def open_database(connection, dbname=""):
    """
    Open a connection to specified database, and save that connection to the active connection object

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :keyword str dbname: name of the database to connect to
    :postcondition: Database named dbname is open in the active ConnectionState object
    :return: Dict with following properties:

        * ``status``: boolean, indicating success or failure of database opening


    """
    if dbname == "":
        '''
        No database specified
        '''
        return {"data.open.open_database": {"status": False}}

    assert (isinstance(connection, ConnectionState))

    try:
        print "connecting ", dbname
        connection.connect_database(dbname)
    except:
        return {"data.open.open_database": {"status": False}}  # failed
    else:
        return {"data.open.open_database": {"status": True}}  # success


def get_database_names(connection):
    """
    Return a list of database names available on the server.

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :return: list of database names
    :rtype: ``list``
    """
    assert (isinstance(connection, ConnectionState))

    dbnames = connection.metadb.get_database_list()
    dbnames = sorted(dbnames, key=str.lower)
    packaged_data = {"data.open.get_database_names": dbnames}
    return packaged_data
