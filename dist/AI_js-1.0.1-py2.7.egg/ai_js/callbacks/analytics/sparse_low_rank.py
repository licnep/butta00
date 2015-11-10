"""
Sparse PCA and related low-rank approximation functions.

:precondition: Database on server must have gone through preprocessing, via ``process_dataset.py``, provided
by ``anser_indicus``.
"""

from anser_indicus.preprocessing.sparse_matrix import SparseMatrix
from anser_indicus.analytics.data_conditioning import tfidf, term_l1_norm, document_l1_norm, duplicate_documents
from anser_indicus.analytics.sparse_low_rank import run_spca
from ai_js.callbacks.connection.connection_state import ConnectionState
from anser_indicus.utilities.utc import iterate_time, get_smallest_time_interval
from anser_indicus.utilities.progress import Progress

thresh = 1e-6


def spca(connection, contentcols=None, focuswords=None, stopwords=None):
    """
    Analyze the current selection

    :precondition: a non-empty selection must be loaded in the
                   :py:attr:`ai_js.callbacks.analytics.connection_state.ConnectionState.db`.

    :param connection: websocket connection state object
    :type connection: :py:class:`ai_js.callbacks.connection.connection_state.ConnectionState`
    :keyword list contentcols: names of columns in database to use in the analysis. Default to ``[]``,
                               meaning that all available content columns are used.
    :keyword list focuswords: words to treat like query terms even if not part of selection. "focus" on said words in analysis, not selection

    :returns: a dict with the following properties:

        1. ``terms``: List of lists, each sublist containing raw text terms
        2. ``docs``: List of lists, each sublist containing document
        3. ``termvs``: List of lists, values corresponding to the numerical weight assigned each word in each topic
        4. ``docvs``: List of lists, values corresponding to the numerical weight assigned each document in each topic
        5. ``n``: Number of documents in the analyzed dataset
        6. ``m``: Number of words in the lexicon for the analyzed dataset

    .. note:: Documents are returned as Python dictionaries, with a key for each column in the database. Note that
              these can be accessed the same way in Javascript, or by using the column names as properties to access
              the desired content.
    """
    if not contentcols:
        contentcols = []
    if not focuswords:
        focuswords = []
    if not stopwords:
        stopwords = []

    focuswords = [x.lower() for x in focuswords]
    stopwords = [x.lower() for x in stopwords]

    assert (isinstance(connection, ConnectionState))

    connection.db.use_content_cols = contentcols

    sm = SparseMatrix()
    sm.attach_database(connection.db.dbname, pool=connection.databasepool)
    #print "about to load from iterator"
    connection.progress.begin(2)
    sm.load_from_iterator(connection.db.iterate_selection(progress=connection.progress))
    #print "SHAPE:", sm.mat.shape
    connection.progress.step()
    #print "loaded!"
    termids = sm.lookup_termids(connection.db.selected_keywords)
    #print "TERMIDS:", termids
    #print "SELECTED KEYWORDS:", connection.db.selected_keywords
    if not termids:
        termids = []
    focustermids = sm.lookup_termids(focuswords)
    #print "FOCUSTERMIDS:", focustermids
    sm.mat = duplicate_documents(sm.mat, termids+focustermids)

    if connection.db.selected_keywords is not None:
        sm.remove_terms(connection.db.selected_keywords)
    print "REMOVED TERMS"

    if stopwords:
        sm.remove_terms(stopwords)

    '''
    Normalize!
    '''
    #A = tfidf(sm.mat)
    A = term_l1_norm(sm.mat)

    print "About to run spca"
    topics = run_spca(A, center='row', card_docs=16, card_terms=36, n_topics=8, progress=connection.progress)
    connection.progress.step()
    #connection.progress.finish()
    # see documentation - topics is a list of tuples
    print "done!"
    terms = []
    termvs = []
    docs = []
    docvs = []
    #subpbar = Progress()
    #subpbar.begin(len(topics))
    for (doci, docv), (termi, termv) in topics:
        #subpbar.step()
        topicterms = []
        topictermvs = []
        topicdocs = []
        topicdocvs = []
        #print "\nTOPIC",i
        for tv, ti in zip(termv, termi):
            #if termv > 0.0:
            if tv > thresh:
                t = sm.lookup_terms([ti])[0]
                topicterms.append(t)
                topictermvs.append(tv)
                #print termv,": ",t
        #print "-----------"
        for dv, di in zip(docv, doci):
            #print docv, doci
            #if docv > 0.0:
            if dv > thresh:
                doc = sm.lookup_docs([di])[0]
                topicdocs.append(doc)
                topicdocvs.append(dv)

        sortedterms = zip(topicterms, topictermvs)
        sortedterms.sort(key=lambda v: v[1], reverse=True)
        terms.append([unicode(x.encode('utf-8').strip()) for x, y in sortedterms])

        termvs.append([y for x, y in sortedterms])
        sorteddocs = zip(topicdocs, topicdocvs)
        sorteddocs.sort(key=lambda v: v[1], reverse=True)
        for x, y in sorteddocs:
            for k, v in x.iteritems():
                if isinstance(v, basestring):
                    x[k] = v.encode('utf-8')
        docs.append([x for x, y in sorteddocs])


        docvs.append([y for x, y in sorteddocs])
    #subpbar.finish()
    #connection.progress.step()
    connection.progress.finish()
    print "Done preparing results"
    print type(terms)
    print type(terms[0])
    print type(terms[0][0])
    for t in terms:  # not printing all of this somehow causes websocket communication to fail... WEIRD BUG!
        for v in t:
            print repr(v)

    packaged_data = {"analytics.sparse_low_rank.spca": {"terms": terms, "docs": docs, "termvs": termvs, "docvs": docvs,
                                                        "n": sm.mat.shape[0], "m": sm.mat.shape[1]}}
    #print packaged_data["analytics.sparse_low_rank.spca"]['terms']
    return packaged_data


def spca_flow(connection, contentcols=None, increment_code=None):
    """
    :keyword increment_code: increment to use for analysis of selection
    :return:
    """
    time_range = connection.db.selection_time_range

    if not contentcols:
        contentcols = []
    if not increment_code:
        increment_code = get_smallest_time_interval(time_range, n_intervals=20)

    assert (isinstance(connection, ConnectionState))

    connection.db.use_content_cols = contentcols
    sm = SparseMatrix()
    sm.attach_database(connection.db.dbname, pool=connection.databasepool)

    # Iterate through time range by increment, get first principal component, normalize and return terms.
    # Turn into an array, each term is represented in every interval.
    interval_topics = []
    for interval in iterate_time(time_range, increment_code):
        sm.load_from_iterator(connection.db.iterate_sub_selection(timerange=interval))

        if sm.mat is None:
            '''
            Then the selection is empty
            '''
            topicterms = []
            topictermvs = []
            interval_topics.append(dict(zip(topicterms, topictermvs)))
            continue

        if connection.db.selected_keywords is not None:
            sm.remove_terms(connection.db.selected_keywords)

        A = term_l1_norm(sm.mat)

        print "About to run spca"
        topic = run_spca(A, center='row', card_docs=16, card_terms=8, n_topics=1, progress=connection.progress)
        (doci, docv), (termi, termv) = topic[0]
        print "topic:", termi
        topicterms = []
        topictermvs = []
        for tv, ti in zip(termv, termi):
            #if termv > 0.0:
            if tv > thresh:
                t = sm.lookup_terms([ti])[0]
                topicterms.append(t)
                topictermvs.append(tv)

        # Normalize termvs
        total = sum(topictermvs)
        topictermvs = [float(x)/float(total) for x in topictermvs]

        # Now, we are done with one interval, add this info to a list and switch to next interval
        interval_topics.append(dict(zip(topicterms, topictermvs)))  # term: value pairs for each interval

    # Format as stack layout for d3
    final_list = []
    total_terms = []
    for topic in interval_topics:
        total_terms += topic.keys()
    total_terms = list(set(total_terms))
    for i, term in enumerate(total_terms):
        final_list.append({"term": term, "values": []})
        #final_list[term] = {"values": []}
        for topic in interval_topics:
            if term not in topic:
                final_list[-1]['values'].append({"x": i, "y": 0.0})
            else:
                final_list[-1]['values'].append({"x": i, "y": topic[term]})
    packaged_data = {"analytics.sparse_low_rank.spca_flow": {"stack_data": final_list}}
    return packaged_data
