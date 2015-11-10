"""
Callback functions used to set up datasets, query information from datasets, etc.
"""

from anser_indicus.data.queryable_database import QueryableDatabase, Selection, CategorySelection, \
    KeywordSelection, TimeSelection

from ai_js.callbacks.connection.connection_state import ConnectionState


def open_database(connection, dbname=""):
    """
    Open a connection to specified database, and save that connection to the connection object
    """
    if dbname == "":
        return {"open_database": {"status": False}}

    assert (isinstance(connection, ConnectionState))

    try:
        print "connecting ", dbname
        connection.connect_database(dbname)
    except:
        print "WHOOPS!"
        #raise
        return {"open_database": {"status": False}}  # failed
    else:
        print "OK!"
        return {"open_database": {"status": True}}  # success


def get_database_names(connection):
    """
    Return a list of database names installed on the system.

    :param connection: object holding state of websocket connection, meta database, etc.
    :type connection: :py:class:`ConnectionState`
    """
    assert (isinstance(connection, ConnectionState))

    dbnames = connection.metadb.get_database_list()
    dbnames = sorted(dbnames, key=str.lower)
    packaged_data = {"get_database_names": dbnames}
    return packaged_data


def get_database_time_range(connection):
    """
    Return the time range (in unix timestamps) of specified database

    :param connection: object holding state of websocket connection, meta database, etc.
    :type connection: :py:class:`ConnectionState`
    """
    assert (isinstance(connection, ConnectionState))
    print "getting time range"
    querydb = connection.db
    print "type querydb:", type(querydb)
    #@TODO: ERROR HANDLING
    time_range = querydb.time_range

    packaged_data = {"get_database_time_range": {"min_time": time_range[0], "max_time": time_range[1]}}

    return packaged_data


def get_database_category_values(connection, colname=""):
    """
    Get list of all distinct values from a column in database.
    """
    assert (isinstance(connection, ConnectionState))

    print "GETTING CATEGORY VALUES"
    querydb = connection.db
    vals = querydb.get_distinct_values_from_col(colname)
    packaged_data = {"get_database_category_values": {"values": vals}}
    return packaged_data


def get_database_binary_intervals(connection, dbname=""):
    """
    """
    assert (isinstance(connection, ConnectionState))

    binary_intervals = connection.metadb.get_binary_interval_codes(dbname).split(',')
    packaged_data = {"get_database_binary_intervals": {"binary_intervals": binary_intervals}}
    return packaged_data


def get_database_installed_binaries(connection, interval_code=""):
    """
    Get the list of binaries for given interval code by UTC tuples.
    """
    assert (isinstance(connection, ConnectionState))
    querydb = connection.db
    intervals = querydb.list_installed_binaries(interval_code)
    print intervals
    packaged_data = {"get_database_installed_binaries": {"installed_intervals": intervals}}  # list of tuples
    return packaged_data


def symbolnews_selection(connection, codes=None, time_range=None):
    """
    Special selection function for the symbolnews spca demo

    Return the size of the selection
    """
    if not time_range:
        time_range = []
    if not codes:
        codes = []
    querydb = connection.db
    assert(isinstance(querydb, QueryableDatabase))
    querydb.clear_selections()

    s = Selection()
    if codes is None or len(codes) == 0 or codes[0] is None:
        s += TimeSelection((time_range[0], time_range[1]))
    else:
        s += CategorySelection("code", codes)
        s &= TimeSelection((time_range[0], time_range[1]))

    print "Made selection", s
    querydb.select(s)
    print "selected!"
    sel_size = querydb.selection_size()
    return {"symbolnews_selection": {"size": sel_size}}


def keyword_selection(connection, keywords=None, time_range=None):
    """
    Select by keywords (OR connected)
    """
    if not time_range: time_range = []
    if not keywords: keywords = []
    querydb = connection.db
    assert(isinstance(querydb,QueryableDatabase))
    querydb.clear_selections()

    s = Selection()
    if keywords is not None:
        keywords = [x for x in keywords if x != '']
    print "KEYWORD_SELECTION",keywords,len(keywords)
    if keywords is None or len(keywords) == 0 or keywords[0] is None:
        print "HELLO WORLD"
        s += TimeSelection((time_range[0],time_range[1]))
    else:
        s += TimeSelection((time_range[0],time_range[1]))
        s &= KeywordSelection(keywords)


    querydb.select(s)
    print "SELECTION COMPLETE"
    sel_size = querydb.selection_size()
    return {"keyword_selection":{"size":sel_size}}


def get_selection_size(connection, dbname=""):
    assert (isinstance(connection, ConnectionState))
    querydb = connection.db
    packaged_data = {"get_selection_size": {"size": querydb.selection_size()}}
    return packaged_data

def get_selection_time_chart(connection,dbname="",n_intervals=1000):
    '''
    Assumes data has already been selected
    '''
    assert (isinstance(connection,ConnectionState))
    querydb = connection.db
    time_chart = querydb.calculate_time_density_chart_from_selection(n_intervals=n_intervals)

    packaged_data = {"get_selection_time_chart":{"time_chart":time_chart}}
    return packaged_data





