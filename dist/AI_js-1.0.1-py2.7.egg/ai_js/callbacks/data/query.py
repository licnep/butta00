"""
Query a database, select and load data

:precondition: a database must be open in the connection state object first
"""

from anser_indicus.data.queryable_database import QueryableDatabase, Selection, TimeSelection, KeywordSelection, \
    AttributeSelection
from anser_indicus.exceptions import AIError
from ai_js.callbacks.connection.connection_state import ConnectionState
from anser_indicus.utilities.utc import INCREMENT_CODES, get_smallest_time_interval


def _build_selection_(list_input):
    """
    Build a selection object from a list of string representations.

    :param list_input: list representing query. Each entry can be a:

        * ``list``: a nested selection
        * ``dict``: key represents type of selection, value is argument for selection
        * ``str``: represents logical connector. Can be:

            * "AND"
            * "OR"
            * "NOT"

    :return: completed selection object
    :rtype: :py:class:`anser_indicus.data.queryable_database.Selection`
    """
    s = Selection()
    connector = "OR"

    for element in list_input:
        subsel = None
        if type(element) is dict:
            print "DICT", element
            if "time" in element:
                time_element = element["time"]
                snap = None
                snap_increment = ""
                database_time_interval = None
                if "snap" in time_element and "snap_increment" in time_element:
                    snap = time_element["snap"]
                    snap_increment = ""
                    if type(time_element["snap_increment"]) is int:
                        # then this specifies an approximate number of intervals desired along range
                        snap_increment = get_smallest_time_interval(time_element["time"],
                                                                    n_intervals=time_element["snap_increment"])
                    elif time_element["snap_increment"] in INCREMENT_CODES:
                        # then this specifies a specific increment to use
                        snap_increment = time_element["snap_increment"]
                    else:
                        continue    # invalid specification, ignore for now
                if "database_time_interval" in time_element:
                    database_time_interval = time_element["database_time_interval"]

                subsel = TimeSelection(time_element["time"], snap=snap, snap_increment=snap_increment, database_time_interval=database_time_interval)
            elif "keyword" in element:
                subsel = KeywordSelection(element["keyword"])
            elif "category" in element:
                subsel = AttributeSelection(element["category"][0], element["category"][1])
            else:
                raise AIError("Invalid selection argument.")
            # now, combine with current selection based on connector

        elif type(element) in (str, unicode):
            print "CONNECTOR", element
            connector = element.upper()

        elif type(element) is list:
            subsel = _build_selection_(element)

        # now, combine!
        if type(element) not in (str, unicode):
            print "CONNECTING"
            if connector == "OR":
                s += subsel
            elif connector == "AND":
                s &= subsel
            elif connector == "NOT":
                s -= subsel

    return s


def select(connection, selection_specification=None, classlabel=0, dontclear=False):
    """
    Construct a selection from a list specification. General multi-purpose function, one-size-fits-all
    interface for querying data.

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :keyword list selection_specification: list representing query. Each entry can be a:

        * ``list``: a nested selection
        * ``dict``: key represents type of selection, value is argument for selection. Keys may be:

            * "keyword": select documents matching one or more keywords
            * "time": select documents matching a specified time range
            * "category": select documents matching a value from a specified column,
                value is a list where first entry is name of category col, second is list of values to match

        * ``str``: represents logical connector. Can be:

            * "AND"
            * "OR"
            * "NOT"

        List can look like: ``[{'keyword',[keyword_list]},CONNECTOR,[selection or specific selection object]...``

    :keyword int classlabel: (optional) specify a numerical class label for a selection, e.g. +1 or -1
    :keyword bool dontclear: (optional) If True, any existing selection will be maintained, and this selection
                             will be appended to the existing selection. Useful when specifying numerical classes
                             for selections.
    :return: dict with properties:

        * ``selection_size``: number of documents in selection. See :py:func:`get_selection_size`.

    """
    connection.db.clear_selections()
    if not selection_specification:
        selection_specification = []
    assert (isinstance(connection, ConnectionState))
    print "about to build", selection_specification
    s = _build_selection_(selection_specification)
    print "about to select"
    connection.db.select(s, classlabel=classlabel, dontclear=dontclear)
    print "selected"

    # once complete, return the size of the selection.
    selection_size = connection.db.selection_size()
    packaged_data = {"data.query.select": {"selection_size": selection_size}}
    print "RETURNING", packaged_data
    return packaged_data


def symbolnews_selection(connection, dbname="", codes=None, time_range=None):
    """
    Special selection function for the symbolnews spca demo

    .. warning:: deprecated. Use :py:func:`select` instead.

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
        s += AttributeSelection("code", codes)
        s &= TimeSelection((time_range[0], time_range[1]))

    print "Made selection", s
    querydb.select(s)
    print "selected!"
    sel_size = querydb.selection_size()
    return {"symbolnews_selection": {"size": sel_size}}


def keyword_selection(connection, dbname="", keywords=None, time_range=None):
    """
    Select by keywords (OR connected)

    .. warning:: deprecated. Use :py:func:`select` instead.
    """
    if not time_range:
        time_range = []
    if not keywords:
        keywords = []
    querydb = connection.db
    assert(isinstance(querydb, QueryableDatabase))
    querydb.clear_selections()

    s = Selection()
    if keywords is not None:
        keywords = [x for x in keywords if x != '']
    print "KEYWORD_SELECTION", keywords, len(keywords)
    if keywords is None or len(keywords) == 0 or keywords[0] is None:
        print "HELLO WORLD"
        s += TimeSelection((time_range[0], time_range[1]))
    else:
        s += TimeSelection((time_range[0], time_range[1]))
        s &= KeywordSelection(keywords)

    querydb.select(s)
    print "SELECTION COMPLETE"
    sel_size = querydb.selection_size()
    return {"keyword_selection": {"size": sel_size}}


def get_selection_size(connection):
    """
    Get the number of documents in the current selection

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :return: dict with properties:

        * ``size``: (int) number of documents in current selection
    """
    assert (isinstance(connection, ConnectionState))
    querydb = connection.db
    packaged_data = {"get_selection_size": {"size": querydb.selection_size()}}
    return packaged_data


def get_selection_time_chart(connection, n_intervals=1000):
    """
    Get a list of times and counts of documents that can be used to plot a time-chart of the density
    of documents over time within selection.

    :precondition: Assumes data has already been selected
    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :keyword int n_intervals: approximate number of datapoints to calculate in time chart.
    :return: dict with properties:

        * ``time_chart``: list of tuples (time, count) pairs, where time is represented as unix timestamps.

    """
    assert (isinstance(connection, ConnectionState))
    querydb = connection.db
    time_chart = querydb.calculate_time_density_chart_from_selection(n_intervals=n_intervals,
                                                                     progress=connection.progress)
    packaged_data = {"data.query.get_selection_time_chart": {"time_chart": time_chart}}
    return packaged_data
