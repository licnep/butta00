"""
Functions that provide information about a database, from time-range to information about the columns in a database.

:precondition: a database must be open in the connection state object first

.. moduleauthor:: Andrew B Godbehere

"""

from ai_js.callbacks.connection.connection_state import ConnectionState
from anser_indicus.exceptions import AIError


def get_database_time_range(connection, increment="", snap=""):
    """
    Get the time range (in unix timestamps) of specified database

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :keyword increment: snap time range to specified increment. If none, don't snap.
    :type increment: `str`
    :returns: a dict with properties:

        * ``min_time``
        * ``max_time``

    """
    assert (isinstance(connection, ConnectionState))
    assert connection.is_database_open()
    print "SPECIFIED INCREMENT:", increment
    # @TODO: ERROR HANDLING
    raw_time_range = connection.db.time_range()
    time_range = connection.db.time_range(increment=increment, snap=snap)

    print "time range:", time_range
    #raise AIError(repr(time_range))
    packaged_data = {"data.inspect.get_database_time_range": {"min_time": time_range[0], "max_time": time_range[1],
                                                              "raw_min_time": raw_time_range[0],
                                                              "raw_max_time": raw_time_range[1]}}
    print "packaged data:", packaged_data
    return packaged_data


def get_database_column_names(connection):
    """
    Get the names of the columns in the connected database table

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :return: dict with properties:

        * ``colinfo``: list of tuples: (name,type) pairs for each column in database

    """
    assert (isinstance(connection, ConnectionState))
    assert connection.is_database_open()

    colinfo = connection.db.db.get_table_columns(connection.db.tblname)
    # colinfo is a list of (name,type) pairs for columns in database
    packaged_data = {"data.inspect.get_database_column_names": {"colinfo": colinfo}}
    return packaged_data


def get_database_category_values(connection, colname=""):
    """
    Get list of all distinct values from a column in database.

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :keyword str colname: name of the column in the database to inspect
    :return: dict with properties:

        * ``values``: list of distinct values in column

    """
    assert (isinstance(connection, ConnectionState))
    assert connection.is_database_open()

    querydb = connection.db
    vals = querydb.get_distinct_values_from_col(colname)
    packaged_data = {"get_database_category_values": {"values": vals}}
    return packaged_data


def get_database_binary_intervals(connection):
    """
    Get the list of time intervals for which matrix binaries have been calculated and saved. Useful for
    fast loading of data by week, month, quarter, year, etc.

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :return: dict with properties:

        * ``binary_intervals``: list of strings representing time intervals.

            * 'd' for day
            * 'w' for week
            * 'm' for month
            * 'q' for quarter
            * 'y' for year


    """
    assert (isinstance(connection, ConnectionState))
    assert connection.is_database_open()
    binary_intervals = connection.metadb.get_binary_interval_codes(connection.db.dbname).split(',')
    packaged_data = {"get_database_binary_intervals": {"binary_intervals": binary_intervals}}
    return packaged_data
