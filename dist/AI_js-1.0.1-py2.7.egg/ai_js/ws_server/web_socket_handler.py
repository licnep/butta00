"""
Web Socket Handler. Accepts websocket messages sent to server, and decides what action to take, and
what message to send as a response. May also send responses without prompting, as a PUSH operation.

WSHandler is to be referenced in socket_server.py, and is not intended to be used directly.
"""

from inspect import getmembers, isfunction, ismodule
import sys
import json
import traceback
from multiprocessing.pool import ThreadPool

import tornado.websocket
from tornado.web import asynchronous
from tornado.ioloop import IOLoop

from ai_js.callbacks import analytics, connection, utilities, data
from urlparse import urlparse

_workers = ThreadPool(10)

'''
@TODO: Progress callback to use IOLoop.instance().add_callback, which is thread safe!
'''


# TODO: Only report a specific exception class?
def exception_catch_wrapper(thisfunc, thisargs, **kwds):
    if not kwds:
        kwds = {}
    try:
        return thisfunc(*thisargs, **kwds)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return {"EXCEPTION": "\n\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))}


def run_background(func, callback, args=(), kwds=None):
    """
    NOTE: the exception only applies to the call to apply_async, not the routine that is run in another process.
    All of those exceptions seem to be lost!

    :param func:
    :param callback:
    :param args:
    :param kwds:
    :return:
    """
    if not kwds:
        kwds = {}

    #def _callback(result):
    #    IOLoop.current().add_callback(lambda: callback(result))
    try:
        #_workers.apply_async(exception_catch_wrapper, (func, args), kwds, _callback)
        _workers.apply_async(exception_catch_wrapper, (func, args), kwds, callback)
    except Exception as e:
        print traceback.format_exc()
        raise e


class WSHandler(tornado.websocket.WebSocketHandler):
    """
    Websocket Handler class (derived from L{tornado.websocket.WebSocketHandler}) to deal with
    open websocket connections and messages. Re-route incoming messages to Python back-end functions
    with the same name.

    :ivar connection: Object used to maintain connection state, database status, etc.
    :type connection: C{L{ConnectionState}}
    :ivar local_message_queue: message queue used to keep messages in order
    :type local_message_queue: C{list}
    :ivar blocking: Flag to indicate whether or not the
    :ivar BACKEND_CALLBACKS: key value pairs of names of callbacks to their instance pointers
    :type BACKEND_CALLBACKS: C{dict}
    """
    def __init__(self, application, request, **kwargs):
        print "INITIALIZING"
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.connection = None
        self.local_message_queue = []
        self.blocking = False
        self.BACKEND_CALLBACKS = {}
        print "WSHandler initialized"

    @property
    def authdb(self):
        return self.application.authdb

    # http://stackoverflow.com/questions/24851207/tornado-403-get-warning-when-opening-websocket
    def check_origin(self, origin):
        parsed_origin = urlparse(origin)
        return parsed_origin.netloc.endswith("sumupanalytics.com")

    def get_current_user(self):
        """
        Read cookie to get the info of the authenticated user
        """
        user_id = self.get_secure_cookie(self.cookie_name)
        print "USER_ID:", user_id
        if not user_id:
            return None
        self.authdb.primary_cursor.execute("SELECT * FROM users WHERE rowid==?;", (int(user_id),))
        return self.authdb.primary_cursor.fetchall()[0]  # provides properties 'email' and 'name'

    def open(self):
        """
        Create callbacks function instance, configure the progressbar handler, send message to indicate
        connection is open.
        """
        print "TRYING TO OPEN"
        if not self.get_current_user():
            self.redirect()
        print "Opening..."
        # callbacks object instance
        self.connection = connection.connection_state.ConnectionState(messagewriter=self.write_message)
        self.connection.progress.display_func = self.progress_update
        
        self.local_message_queue = []
        self.blocking = False
        
        self.BACKEND_CALLBACKS = {}        

        # Automatically import packages and get function names, while maintaining naming scope
        for subpackagename, subpackage in {"analytics": analytics, "connection": connection,
                                           "data": data, "utilities": utilities}.iteritems():
            package_contents = getmembers(subpackage, ismodule)
            self.BACKEND_CALLBACKS[subpackagename] = {}
            for modname, mod in package_contents:
                mod_contents = getmembers(mod, isfunction)
                self.BACKEND_CALLBACKS[subpackagename][modname] = {}
                self.BACKEND_CALLBACKS[subpackagename][modname].update([o for o in mod_contents])

        #for p in subpackages:
            # import and get the modules
        #    from

        #for name in extension_names:
        #    self.BACKEND_CALLBACK.update(dict([o for o in getmembers()]))        

        # get all functions from connection_state module
        #self.BACKEND_CALLBACKS.update(dict([o for o in getmembers(data_management, isfunction)]))
        #self.BACKEND_CALLBACKS.update(dict([o for o in getmembers(progress, isfunction)]))
        #self.BACKEND_CALLBACKS.update(dict([o for o in getmembers(sparse_low_rank_approximation, isfunction)]))
        
        #self.connection.progress.on_update = self.progress_update   # what to do on progress update
        #self.connection.progress.on_complete = self.progress_complete

        #self.connection.messagewriter = self.write_message
        
        print 'Connection opened.'
        #print self.BACKEND_CALLBACKS.keys()
        self.write_message(json.dumps({"open": "websocket is connected"}))  # send an opening message
    
    #@tornado.web.authenticated
    #@asynchronous
    def on_message(self, message):
        """
        Define how to handle incoming websocket messages. Each message should indicate a funciton
        to call from the backend callbacks, along with any necessary arguments.
        Message can be an aggregate, a list of function calls to perform as one action.

        :param message: message passed by tornado to this handler.
        :type message: ``str``, JSON format
        """
        print "Message received"
        if not self.get_current_user():
            return None

        # print self, threading.current_thread()
        msgobj = json.loads(message)   # read message and load JSON object
        # should be a JSON object, where each key is a function to call,
        # and each value are the parameters for the function

        for fcn_name in msgobj.keys():
            # each key should be a function call, value should be parameters, as a dictionary.
            print "FCNNAME:", fcn_name

            #
            # if fcn_name == "LOGOUT":
            #     self.clear_cookie("sumup_user")
            #     # TODO: Redirect to main page
            #     continue

            fcn_name_components = fcn_name.split('.')
            o = None
            try:
                for i, comp in enumerate(fcn_name_components):
                    #print "i,",i,"comp,",comp
                    #print o
                    if i == 0:
                        o = self.BACKEND_CALLBACKS[comp]
                    else:
                        o = o[comp]
            except:
                print "Invalid function called"
                continue

            params = msgobj[fcn_name]
            #print "params:", params

            if self.blocking is False:
                self.local_message_queue.append((o, params))
                self.blocking = True

                if params is None:
                #raise e
                #self.write_message(json.dumps({"exception":str(e)}))
                    print "NO PARAMS"
                    print "running", o, "in background"
                    run_background(o, self.on_complete, (self.connection,))
                else:
                    print "CALLING"
                    run_background(o, self.on_complete, (self.connection,), params)  # specify keyword arguments
            else:
                self.local_message_queue.append((o, params))

    def on_complete(self, res):
        """
        Called when process completes. Update the message queue here?
        """
        if "EXCEPTION" in res:
            print "EXCEPTION", res["EXCEPTION"]
            error_message = utilities.errors.raise_error(message=res["EXCEPTION"])
            self.write_message(error_message)
            return

        #print "COMPLETE", res
        self.local_message_queue.pop(0)
        if len(self.local_message_queue) == 0:
            self.blocking = False
        else:
            # call next message
            params = self.local_message_queue[0][1]
            o = self.local_message_queue[0][0]
            if params is None:
                #raise e
                #self.write_message(json.dumps({"exception":str(e)}))
                #print "NO PARAMS"
                #print 'on complete running',o
                run_background(o, self.on_complete, (self.connection,))
            else:
                #print "CALLING"
                run_background(o, self.on_complete, (self.connection,), params)  # specify keyword arguments

        returnmsg = {}
        if res is not None and res.__class__ == {}.__class__:
            returnmsg[res.keys()[0]] = res[res.keys()[0]]
        else:
            returnmsg = ""

        self.write_message(json.dumps(returnmsg))

    def progress_update(self, value, msgs, is_done):
        """
        Call this to send a message to update a progress bar element
        """
        if is_done:            
            self.progress_complete()
        else:
            result = {"progress_update": {"value": value, "message": msgs}}
            IOLoop.current().add_callback(lambda: self.write_message(json.dumps(result)))
            #self.write_message(json.dumps(result))
    
    def progress_complete(self):
        """
        """
        result = {"progress_update": {"value": 100, "message": "Complete!"}}
        #self.write_message(json.dumps(result))        
        IOLoop.current().add_callback(lambda: self.write_message(json.dumps(result)))

    def on_close(self):
        self.connection.close()
        print 'Connection closed.'